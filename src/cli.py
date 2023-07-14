import argparse
import os

from rich.live import Live
from rich.markdown import Markdown

from cli_help import SHORTCUTS_HELP
from conversation_exporter import ConversationExporter

from revChatGPT.V1 import Chatbot
from revChatGPT.utils import create_session, create_completer, get_input
from revChatGPT.typings import CLIError, C

from app import load_config
from commands import Commands
from common import GPT_MODELS, print_md, try_chatbot
from conversation_cache import ConversationCache
from json_config import JsonConfig


WELCOME_MESSAGE = f'''
{C.OKGREEN}ChatGPT Command Tool{C.ENDC}

{C.OKCYAN}    .help{C.ENDC}       Show All Commands
{C.OKCYAN}Alt+Enter{C.ENDC}   Send Message / Execute Command
'''


class ChatbotCli:
    def __init__(self, config: dict):
        self.__config = config.copy()
        self.__save = JsonConfig('save.json')
        self.__commands = Commands()
        self.__chatbot = Chatbot(
            self.__config,
            conversation_id=self.__config.get('conversation_id'),
            parent_id=self.__config.get('parent_id'),
        )
        self.__exporter = ConversationExporter(self.__config['export_dir'], self.__chatbot)
        self.__cache = None
        
        self.__commands.add('.show_shortcuts', 'Show short cuts', self.__show_shortcuts)
        self.__commands.add('.new', 'Start new conversation', self.__new_conversation)
        self.__commands.add('.exit', 'Exit command line', exit)
        self.__commands.add('.change_title', 'Change the title of the current conversation', self.__change_title)
        self.__commands.add('.set_conversation', f'{C.HEADER}P1: cid{C.ENDC}. Set the current conversation to cid', self.__set_conversation)
        self.__commands.add('.show_messages', 'Show all messages in the current conversation', self.__show_msgs)
        self.__commands.add('.show_conversations', 'List all conversations', self.__list_conversations)
        self.__commands.add('.set_model', f'{C.HEADER}P1: model{C.ENDC}. Set model, valid models: {C.HEADER}{", ".join(GPT_MODELS.keys())}{C.ENDC}', self.__set_model)
        self.__commands.add('.export', f'{C.HEADER}P1: cid{C.ENDC}, export conversation', self.__export_conversation)
        self.__commands.add('.export_all', 'export all conversations', self.__export_all_conversations)
        self.__commands.add('.delete', f'{C.HEADER}[P1: cid]{C.ENDC}. Delete conversation(current or cid)', self.__delete_conversation)
        self.__commands.add('.delete_all', 'Delete all conversations', self.__delete_all_conversations)
        self.__commands.add('.show_config', 'Show config', self.__show_config)

    def __get_cache(self) -> ConversationCache:
        if self.__cache is None:
            self.__cache = ConversationCache(self.__chatbot.get_conversations(limit=100))
        return self.__cache
    
    def __clear_cache(self) -> None:
        self.__cache = None

    @try_chatbot
    def __ask(self, prompt):
        message_id = 0
        with Live(auto_refresh=False, vertical_overflow='visible') as live:
            for data in self.__chatbot.ask(prompt, auto_continue=True):
                live.update(Markdown(data['message']), refresh=True)
                message_id = data['parent_id']
        self.__save.set('conversation_id', self.__chatbot.conversation_id)
        self.__save.save()

        cache = self.__get_cache()
        if self.__chatbot.conversation_id and cache.get_index(self.__chatbot.conversation_id) == -1:
            title = self.__chatbot.gen_title(self.__chatbot.conversation_id, message_id)
            conversation = {
                'id': self.__chatbot.conversation_id,
                'title': title,
            }
            print(f'\n{C.OKCYAN}{title}{C.ENDC} created.')
            cache.add(conversation)

        if self.__config.get('auto_export'):
            title = cache.get_title(cache.get_index(self.__chatbot.conversation_id))
            self.__exporter.export(self.__chatbot.conversation_id, title)

    def __check_export_dir(self) -> bool:
        export_dir = self.__config.get('export_dir')
        if not export_dir:
            print(f'{C.WARNING}export_dir is not set in config.json{C.ENDC}')
            return False
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        if not os.path.isdir(export_dir):
            raise Exception(f'export_dir: {export_dir} is not a directory')
        return True
    
    def __confirm(self, prompt: str, default: bool = False) -> bool:
        if default:
            prompt += ' [Y/n]'
        else:
            prompt += ' [y/N]'
        
        print(prompt)
        while True:
            answer = get_input().strip().lower()
            if answer == '':
                return default
            if answer in ['y', 'yes']:
                return True
            if answer in ['n', 'no']:
                return False
            print('Invalid answer')

    
    def run(self):
        if not self.__check_export_dir():
            return False
        
        print(WELCOME_MESSAGE)
        print(f'Model: {C.WARNING}{self.__config["model"]}{C.ENDC}')
        print()

        conversation_id = self.__save.get('conversation_id')
        if conversation_id:
            try:
                if self.__chatbot.get_msg_history(conversation_id):
                    self.__chatbot.conversation_id = conversation_id                
                self.__show_msgs([])
            except Exception:
                self.__save.set('conversation_id', None)
                self.__save.save()
        
        if self.__save.get('conversation_id') is None:
            self.__list_conversations([])
        print()

        session = create_session()
        completer1 = create_completer(self.__commands.names + self.__exporter.all_titles)
        completer2 = create_completer(self.__commands.names)
        try:
            while True:
                print(f'{C.OKBLUE + C.BOLD}You: {C.ENDC}')

                completer = completer1 if self.__chatbot.conversation_id is None else completer2
                prompt = get_input(session=session, completer=completer)
                if self.__chatbot.conversation_id is None:
                    if self.__exporter.has_conversation(prompt):
                        self.__exporter.print_conversation(prompt)
                        continue

                if self.__commands.handle(prompt):
                    print()
                    continue

                print()
                print(f'{C.OKGREEN + C.BOLD}ChatGPT: {C.ENDC}')

                self.__ask(prompt)

                print()
        except (KeyboardInterrupt, EOFError):
            exit()
        except Exception as exc:
            error = CLIError('command line program unknown error')
            raise error from exc

    def __show_shortcuts(self, args: list[str]):
        print(SHORTCUTS_HELP)
    
    def __new_conversation(self, args: list[str]):
        self.__chatbot.reset_chat()
        self.__save.set('conversation_id', None)
        self.__save.save()
        print(f'{C.OKCYAN}New conversation started.{C.ENDC}')

    @try_chatbot
    def __list_conversations(self, args: list[str]):
        if len(args) == 2:
            if args[1] == '-s':
                self.__clear_cache()

        cache = self.__get_cache()
        titles = cache.titles()
        if len(titles) == 0:
            print(f'{C.WARNING}No conversation.{C.ENDC}')
            return

        current_cid = self.__chatbot.conversation_id
        for i, title in enumerate(titles):
            if cache.get_cid(i) == current_cid:
                print(f'{i:<3}: {C.OKCYAN}{title}{C.ENDC} {C.OKGREEN}(current){C.ENDC}')
            else:
                print(f'{i:<3}: {C.OKCYAN}{title}{C.ENDC}')

    def __set_model(self, args: list[str]):
        if len(args) == 2:
            model = args[1]
            if model not in GPT_MODELS:
                print(f'{C.WARNING}Invalid mode.{C.ENDC}')
                return
            self.__config['model'] = GPT_MODELS[model]
            print(f'Model set to {C.WARNING}{GPT_MODELS[model]}.{C.ENDC}')
        else:
            print(f'{C.WARNING}Invalid arguments.{C.ENDC}')
            print(f'Usage: .set_model <model>, model in {C.HEADER}{", ".join(GPT_MODELS.keys())}{C.ENDC}')

    def __export_conversation(self, args: list[str]):
        cache = self.__get_cache()
        if len(args) == 2:
            try:
                index = int(args[1])
            except ValueError:
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            if not cache.exist(index):
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            conversation_id = cache.get_cid(index)
            if not conversation_id:
                print(f'{C.WARNING}No conversation to export.{C.ENDC}')
                return
        else:
            conversation_id = self.__chatbot.conversation_id
            if not conversation_id:
                print(f'{C.WARNING}No conversation to export.{C.ENDC}')
                return
            index = cache.get_index(conversation_id)
        
        path = self.__exporter.export(conversation_id, cache.get_title(index))
        print(f'Save to: {path}')

    def __export_all_conversations(self, args: list[str]):
        cache = self.__get_cache()
        for index in range(len(cache)):
            path = self.__exporter.export(cache.get_cid(index), cache.get_title(index))
            print(f'Save to: {path}')

    @try_chatbot
    def __delete_conversation(self, args: list[str]):
        cache = self.__get_cache()
        if len(args) == 2:
            try:
                index = int(args[1])
            except ValueError:
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            if not cache.exist(index):
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            conversation_id = cache.get_cid(index)
        else:
            conversation_id = self.__chatbot.conversation_id
            if not conversation_id:
                print(f'{C.WARNING}No conversation to delete.{C.ENDC}')
                return
            index = cache.get_index(conversation_id)
        
        if not conversation_id:
            print(f'{C.WARNING}No conversation to delete.{C.ENDC}')
            return

        title = cache.get_title(index)
        self.__chatbot.delete_conversation(conversation_id)
        cache.delete(index)
        print(f'session {C.OKCYAN}{title}{C.ENDC} successfully delete.')

        if self.__config['auto_export']:
            self.__exporter.delete(title)

        if conversation_id == self.__chatbot.conversation_id:
            self.__chatbot.conversation_id = None
            self.__save.set('conversation_id', None)
            self.__save.save()

    def __delete_all_conversations(self, args: list[str]):
        if not self.__confirm('Are you sure to delete all conversations?'):
            return
        self.__chatbot.clear_conversations()
        print(f'{C.OKCYAN}All conversations successfully deleted.{C.ENDC}')
        self.__clear_cache()
        self.__chatbot.conversation_id = None
        self.__save.set('conversation_id', None)
        self.__save.save()

    @try_chatbot
    def __show_msgs(self, args: list[str]):
        if self.__chatbot.conversation_id is None:
            print(f'{C.WARNING}No conversation to show messages.{C.ENDC}')
            return
        
        history = self.__chatbot.get_msg_history(self.__chatbot.conversation_id, 'utf-8')
        print(f'{C.OKCYAN + C.BOLD}Title: {history["title"]}{C.ENDC}\n') # type: ignore

        mapping = history['mapping'] # type: ignore
        messages = [msg['message'] for msg in mapping.values() if 'message' in msg and 'content' in msg['message']]

        for msg in messages:
            content_type = msg['content']['content_type']
            if content_type != 'text':
                continue

            text = msg['content']['parts'][0]
            if not text.strip():
                continue

            if msg['author']['role'] == 'assistant':
                print(f'{C.OKGREEN}ChatGPT:{C.ENDC}')
                print_md(text)
            elif msg['author']['role'] == 'user':
                print(f'{C.OKBLUE}You:{C.ENDC}')
                print_md(text)
            
            print('')

    def __set_conversation(self, args: list[str]):
        try:
            index = int(args[1])
            cache = self.__get_cache()
            if not cache.exist(index):
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return

            conversation_id = cache.get_cid(index)
            self.__chatbot.conversation_id = conversation_id
            print(f'Conversation successfully set to {C.OKCYAN}{cache.get_title(index)}{C.ENDC}.\n')
            self.__save.set('conversation_id', conversation_id)
            self.__save.save()
            self.__show_msgs([])
        except IndexError:
            print(f'{C.WARNING}Invalid index.{C.ENDC}')
        except Exception as e:
            print(f'{C.WARNING}{e}{C.ENDC}')

    def __show_config(self, args: list[str]):
        print(f'{C.OKCYAN + C.BOLD}      Model:{C.ENDC} {self.__chatbot.config["model"]}')
        print(f'{C.OKCYAN + C.BOLD} Export Dir:{C.ENDC} {self.__chatbot.config["export_dir"]}')
        print(f'{C.OKCYAN + C.BOLD}Auto Export:{C.ENDC} {self.__chatbot.config["auto_export"]}')

    @try_chatbot
    def __change_title(self, args: list[str]):
        if self.__chatbot.conversation_id is None:
            print(f'{C.WARNING}No conversation to change title.{C.ENDC}')
            return True
        
        if len(args) == 1:
            print(f'{C.WARNING}No title specified.{C.ENDC}')
            return True

        title = ' '.join(args[1:])
        cache = self.__get_cache()
        cid = self.__chatbot.conversation_id
        self.__chatbot.change_title(cid, title)
        index = cache.get_index(cid)

        if self.__config['auto_export']:
            self.__exporter.rename(cid, cache.get_title(index), title)

        cache.set_title(index, title)

        print(f'Conversation title successfully changed to {C.OKCYAN}{title}{C.ENDC}.')    


def __parse_args():
    parser = argparse.ArgumentParser(description='Chatgpt Command Line Tool')
    parser.add_argument('-m', '--model', type=str, default='3.5',
                        help='gpt model, 3.5 or 4, default 3.5')
    parser.add_argument('-cfg', '--config', help='config file path')

    return parser.parse_args()


def __load_cmd_config() -> dict:
    args = __parse_args()
    config = load_config(args.config)
    if args.model in GPT_MODELS:
        config['model'] = GPT_MODELS[args.model]
    return config


if __name__ == '__main__':
    config = __load_cmd_config()
    mgr = ChatbotCli(config)
    mgr.run()
