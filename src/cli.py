import json
import logging
import argparse
import time

from typing import NoReturn

from revChatGPT.V1 import Chatbot
from revChatGPT.utils import create_session, create_completer, get_input
from revChatGPT.typings import colors, CLIError

from asker import load_config
from json_config import JsonConfig

C = colors()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
)

log = logging.getLogger(__name__)
save = JsonConfig('save.json')

MAX_RETRIES = 10

def try_chatbot(func: callable) -> callable:
    def wrapper(*args):
        for i in range(0, MAX_RETRIES):
            try:
                return func(*args)
            except Exception as e:
                print(f'Error:{e}')
                print(f'\n[{i+1}/{MAX_RETRIES}] Retrying in 3 seconds')
                time.sleep(3)
        raise CLIError(f'Retries exceeded {MAX_RETRIES}')

    return wrapper


class CommandItem:
    def __init__(self, name: str, help: str, func: callable):
        self.name = name
        self.help = help
        self.func = func


class Commands:
    def __init__(self):
        self.commands = []
        self.add('!help', 'Show this message', lambda _: print(self.get_help()))

    def add(self, name: str, help: str, func: callable):
        self.commands.append(CommandItem(name, help, func))

    def get_help(self) -> str:
        return '\n'.join([f'\t{item.name} - {item.help}' for item in self.commands])

    def get_names(self) -> list[str]:
        return [item.name for item in self.commands]

    def handle(self, command: str) -> bool:
        command = command.strip()
        if command.startswith('!'):
            command = command.lower()

        args = command.split(' ')
        command_name = args[0]
        for item in self.commands:
            if item.name == command_name:
                item.func(args)
                return True
        return False


def main(config: dict) -> NoReturn:
    chatbot = Chatbot(
        config,
        conversation_id=config.get('conversation_id'),
        parent_id=config.get('parent_id'),
    )

    def new_conversation(args: list[str]):
        chatbot.reset_chat()
        print('New conversation started.')

    @try_chatbot
    def list_conversations(args: list[str]):
        for conv in chatbot.get_conversations(limit=100):
            print(f'{conv.get("title")} - {conv.get("id")}')

    @try_chatbot
    def delete_conversation(args: list[str]):
        if len(args) == 2:
            conversation_id = args[1]
        else:
            conversation_id = chatbot.conversation_id
        
        if not conversation_id:
            print('No conversation to delete.')
            return True

        chatbot.delete_conversation(conversation_id)
        print(f'session [{conversation_id}] successfully delete.')

        if conversation_id == chatbot.conversation_id:
            chatbot.conversation_id = None
            save.set('conversation_id', None)
            save.save()

    def rollback(args: list[str]):
        try:
            rollback = int(args[1])
        except IndexError:
            logging.exception(
                'No number specified, rolling back 1 message',
                stack_info=True,
            )
            rollback = 1
        chatbot.rollback_conversation(rollback)
        print(f'Rolled back {rollback} messages.')
    
    def set_conversation(args: list[str]):
        try:
            conversation_id = args[1]
            chatbot.conversation_id = conversation_id
            print(f'Conversation successfully set to {conversation_id}.\n')
            save.set('conversation_id', conversation_id)
            save.save()
            show_msgs([])
        except IndexError:
            print('Please include conversation UUID in command')

    @try_chatbot
    def show_msgs(args: list[str]):
        if chatbot.conversation_id is None:
            print('No conversation to show messages.')
            return True
        history = chatbot.get_msg_history(chatbot.conversation_id, 'utf-8')
        print(f'{C.OKCYAN + C.BOLD}Title: {history["title"]}{C.ENDC}\n')

        mapping = history['mapping']
        messages = [msg['message'] for msg in mapping.values() if 'message' in msg and 'content' in msg['message']]

        for msg in messages:
            text = msg['content']['parts'][0]
            if not text.strip():
                continue

            if msg['author']['role'] == 'assistant':
                print(f'{C.OKBLUE}You:{C.ENDC}\n{text}\n')
            elif msg['author']['role'] == 'user':
                print(f'{C.OKGREEN}ChatGPT:{C.ENDC}\n{text}\n')
            
    
    def show_config(args: list[str]):
        print('Current config:')
        print(json.dumps(chatbot.config, indent=4))
    
    @try_chatbot
    def delete_none_title_conversations(args: list[str]):
        print('Deleting all conversations without title...')
        count = 0
        for conv in chatbot.get_conversations(limit=100):
            if conv.get('title') == 'New chat':
                conversation_id = conv.get('id')
                chatbot.delete_conversation(conversation_id)
                print(f'session [{conversation_id}] successfully delete.')
                if conversation_id == chatbot.conversation_id:
                    chatbot.conversation_id = None
                    save.set('conversation_id', None)
                    save.save()

                count += 1
        print(f'{count} conversations deleted.')
    
    @try_chatbot
    def change_title(args: list[str]):
        if chatbot.conversation_id is None:
            print('No conversation to change title.')
            return True
        
        if len(args) == 1:
            print('No title specified.')
            return True

        chatbot.change_title(chatbot.conversation_id, args[1])
        print(f'Conversation title successfully changed to {args[1]}.')

    commands = Commands()
    commands.add('!new', 'Start new conversation', new_conversation)
    commands.add('!change_title', 'Change the title of the current conversation', change_title)
    commands.add('!set_conversation', 'P1: cid. Set the current conversation to cid', set_conversation)
    commands.add('!show_msgs', 'Show all messages in the current conversation', show_msgs)
    commands.add('!rollback', 'P1: n, Rollback n messages', rollback)
    commands.add('!conversations', 'List all conversations', list_conversations)
    commands.add('!delete', 'P1: sid. Delete conversation with sid or current conversation', delete_conversation)
    commands.add('!delete_none_title', 'Delete all conversations without title', delete_none_title_conversations)
    commands.add('!config', 'Show config', show_config)

    conversation_id = save.get('conversation_id')
    if conversation_id:
        try:
            if chatbot.get_msg_history(conversation_id):
                chatbot.conversation_id = conversation_id
            show_msgs([])
        except Exception:
            save.set('conversation_id', None)
            save.save()

    run_cli(chatbot, commands)


def run_cli(chatbot: Chatbot, commands: Commands):
    session = create_session()
    completer = create_completer(commands.get_names())
    print()
    try:
        while True:
            print(f'{C.OKBLUE + C.BOLD}You: {C.ENDC}')

            prompt = get_input(session=session, completer=completer)
            if commands.handle(prompt):
                continue

            print()
            print(f'{C.OKGREEN + C.BOLD}ChatGPT: {C.ENDC}')

            ask(chatbot, prompt)

            print(C.ENDC)
            print()
    except (KeyboardInterrupt, EOFError):
        exit()
    except Exception as exc:
        error = CLIError('command line program unknown error')
        raise error from exc


@try_chatbot
def ask(chatbot, prompt):
    prev_text = ''
    for data in chatbot.ask(prompt, auto_continue=True):
        message = data['message'][len(prev_text):]
        print(message, end='', flush=True)
        prev_text = data['message']
    save.set('conversation_id', chatbot.conversation_id)
    save.save()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Chatgpt Command Line Tool')
    parser.add_argument('-m', '--mode', type=str, default='3.5',
                        help='gpt mode, 3.5 or 4, default 3.5')

    return parser.parse_args()


def load_cmd_config() -> dict:
    config = load_config()
    args = parse_args()
    if args.mode == '3.5':
        config['model'] = 'gpt-3.5-turbo'
    elif args.mode == '4':
        config['model'] = 'gpt-4'
    return config


WELCOME_MESSAGE = f'''
    ChatGPT Command Tool (https://chat.openai.com/chat)

    !help       -> Show All Commands
    Esc, Enter  -> send message
    Alt+Enter   -> send message
'''

if __name__ == '__main__':
    config = load_cmd_config()

    print(WELCOME_MESSAGE)
    main(config)
