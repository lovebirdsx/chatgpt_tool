import json
import logging
import argparse
import os
import time

from rich import print as print_rich
from rich.live import Live
from rich.markdown import Markdown

from typing import NoReturn

from revChatGPT.V1 import Chatbot
from revChatGPT.utils import create_session, create_completer, get_input
from revChatGPT.typings import CLIError, Colors

from app import load_config
from commands import Commands
from common import to_valid_filename
from conversation_cache import ConversationCache
from json_config import JsonConfig

C = Colors()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
)

log = logging.getLogger(__name__)
save = JsonConfig('save.json')

MAX_RETRIES = 5

def try_chatbot(func: callable) -> callable:
    def wrapper(*args):
        for i in range(0, MAX_RETRIES):
            try:
                return func(*args)
            except Exception as e:
                print(f'{C.FAIL}Error [{i+1}/{MAX_RETRIES}]{C.ENDC}:{e}')
                if i < MAX_RETRIES - 1:
                    print(f'\nRetrying in 3 seconds...\n')
                    time.sleep(3)
        
        time.sleep(0.5)
        print('')
        print(f'{C.BOLD}{C.FAIL}Error: Failed to retry {MAX_RETRIES} times{C.ENDC}')
    
    return wrapper

def print_md(msg, **kwargs):
    print_rich(Markdown(msg), **kwargs)


def confirm(prompt: str, default: bool = False) -> bool:
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


_cache: ConversationCache = None
def get_conversation_cache(chatbot: Chatbot) -> ConversationCache:
    global _cache
    if _cache is None:
        _cache = ConversationCache(chatbot.get_conversations(limit=100))
    return _cache


def clear_conversation_cache():
    global _cache
    _cache = None


@try_chatbot
def get_history(chatbot: Chatbot, cid: str) -> list[dict]:
    history = chatbot.get_msg_history(cid, 'utf-8')
    return history


def check_export_dir(config: dict) -> bool:
    export_dir = config.get('export_dir')
    if not export_dir:
        print(f'{C.WARNING}export_dir is not set in config.json{C.ENDC}')
        return False
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    if not os.path.isdir(export_dir):
        raise Exception(f'export_dir: {export_dir} is not a directory')
    return True


def save_conversation(chatbot: Chatbot, cid: str, title: str, path: str) -> NoReturn:
    history = get_history(chatbot, cid)
    mapping = history['mapping']
    messages = [msg['message'] for msg in mapping.values() if 'message' in msg and 'content' in msg['message']]

    # 将messages写入文件
    with open(path, 'w', encoding='utf8') as f:
        f.write(f'# {title}\n\n')
        for msg in messages:
            text = msg['content']['parts'][0]
            if not text.strip():
                continue

            if msg['author']['role'] == 'assistant':
                f.write(f'ChatGPT:\n{text}\n\n')
            elif msg['author']['role'] == 'user':
                f.write(f'You:\n{text}\n\n')
    print(f'Save to: {os.path.normpath(path)}')


def main(config: dict) -> NoReturn:
    chatbot = Chatbot(
        config,
        conversation_id=config.get('conversation_id'),
        parent_id=config.get('parent_id'),
    )

    def new_conversation(args: list[str]):
        chatbot.reset_chat()
        print(f'{C.OKCYAN}New conversation started.{C.ENDC}')

    @try_chatbot
    def list_conversations(args: list[str]):
        if len(args) == 2:
            if args[1] == '-s':
                clear_conversation_cache()

        cache = get_conversation_cache(chatbot)
        titles = cache.titles()
        if len(titles) == 0:
            print(f'{C.WARNING}No conversation.{C.ENDC}')
            return

        for i, title in enumerate(titles):
            print(f'{i:<3}: {C.OKCYAN}{title}{C.ENDC}')
    
    def export_conversation(args: list[str]):
        if len(args) == 2:
            try:
                index = int(args[1])
            except ValueError:
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            cache = get_conversation_cache(chatbot)
            if not cache.exist(index):
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            conversation_id = cache.get_id(index)
        else:
            conversation_id = chatbot.conversation_id
        
        if not conversation_id:
            print(f'{C.WARNING}No conversation to export.{C.ENDC}')
            return
        
        if not check_export_dir(config):
            return

        save_path = f'{config.get("export_dir")}/{to_valid_filename(cache.get_title(index))}.md'
        save_conversation(chatbot, conversation_id, cache.get_title(index), save_path)

    def export_all_conversations(args: list[str]):
        if not check_export_dir(config):
            return

        cache = get_conversation_cache(chatbot)
        for index in range(len(cache)):
            save_path = f'{config.get("export_dir")}/{to_valid_filename(cache.get_title(index))}.md'
            save_conversation(chatbot, cache.get_id(index), cache.get_title(index), save_path)

    @try_chatbot
    def delete_conversation(args: list[str]):
        cache = get_conversation_cache(chatbot)
        index = 0
        if len(args) == 2:
            try:
                index = int(args[1])
            except ValueError:
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            if not cache.exist(index):
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return
            
            conversation_id = cache.get_id(index)
        else:
            conversation_id = chatbot.conversation_id
        
        if not conversation_id:
            print(f'{C.WARNING}No conversation to delete.{C.ENDC}')
            return

        chatbot.delete_conversation(conversation_id)
        title = cache.get_title(index)
        cache.delete(index)
        print(f'session {C.OKCYAN}{title}{C.ENDC} successfully delete.')

        if conversation_id == chatbot.conversation_id:
            chatbot.conversation_id = None
            save.set('conversation_id', None)
            save.save()

    def delete_all_conversations(args: list[str]):
        if not confirm('Are you sure to delete all conversations?'):
            return
        chatbot.clear_conversations()
        print(f'{C.OKCYAN}All conversations successfully deleted.{C.ENDC}')
        clear_conversation_cache()
        chatbot.conversation_id = None
        save.set('conversation_id', None)
        save.save()

    def rollback(args: list[str]):
        if chatbot.conversation_id is None:
            print(f'{C.WARNING}No conversation to rollback.{C.ENDC}')
            return

        try:
            rollback = int(args[1])
        except IndexError:
            rollback = 1
        chatbot.rollback_conversation(rollback)
        print(f'Rolled back {rollback} messages.')
    
    def set_conversation(args: list[str]):
        try:
            index = int(args[1])
            cache = get_conversation_cache(chatbot)
            if not cache.exist(index):
                print(f'{C.WARNING}Invalid index.{C.ENDC}')
                return

            conversation_id = cache.get_id(index)
            chatbot.conversation_id = conversation_id
            print(f'Conversation successfully set to {C.OKCYAN}{cache.get_title(index)}{C.ENDC}.\n')
            save.set('conversation_id', conversation_id)
            save.save()
            show_msgs([])
        except IndexError:
            print(f'{C.WARNING}Please include conversation UUID in command{C.ENDC}')

    @try_chatbot
    def show_msgs(args: list[str]):
        if chatbot.conversation_id is None:
            print(f'{C.WARNING}No conversation to show messages.{C.ENDC}')
            return
        
        history = chatbot.get_msg_history(chatbot.conversation_id, 'utf-8')
        print(f'{C.OKCYAN + C.BOLD}Title: {history["title"]}{C.ENDC}\n')

        mapping = history['mapping']
        messages = [msg['message'] for msg in mapping.values() if 'message' in msg and 'content' in msg['message']]

        for msg in messages:
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
            
    
    def show_config(args: list[str]):
        print('Current config:')
        print(json.dumps(chatbot.config, indent=4))
    
    @try_chatbot
    def delete_none_title_conversations(args: list[str]):
        print('Deleting all conversations without title...')
        count = 0
        cache = get_conversation_cache(chatbot)
        
        conversations = [conv for conv in cache.conversations if conv.get('title') == 'New chat']
        for conv in conversations:
            id = conv.get('id')
            chatbot.delete_conversation(id)
            index = cache.get_index(id)
            title = cache.get_title(index)
            cache.delete(index)
            print(f'session {C.OKCYAN}{title}{C.ENDC} successfully delete.')
            count += 1

            if id == chatbot.conversation_id:
                chatbot.conversation_id = None
                save.set('conversation_id', None)
                save.save()
                
        print(f'{count} conversations deleted.')
    
    @try_chatbot
    def change_title(args: list[str]):
        if chatbot.conversation_id is None:
            print(f'{C.WARNING}No conversation to change title.{C.ENDC}')
            return True
        
        if len(args) == 1:
            print(f'{C.WARNING}No title specified.{C.ENDC}')
            return True

        title = ' '.join(args[1:])
        cache = get_conversation_cache(chatbot)
        chatbot.change_title(chatbot.conversation_id, title)
        index = cache.get_index(chatbot.conversation_id)
        cache.set_title(index, title)

        print(f'Conversation title successfully changed to {C.OKCYAN}{title}{C.ENDC}.')

    commands = Commands()
    commands.add('!new', 'Start new conversation', new_conversation)
    commands.add('!change_title', 'Change the title of the current conversation', change_title)
    commands.add('!set_conversation', 'P1: cid. Set the current conversation to cid', set_conversation)
    commands.add('!show_msgs', 'Show all messages in the current conversation', show_msgs)
    commands.add('!rollback', 'P1: n, Rollback n messages', rollback)
    commands.add('!conversations', 'List all conversations', list_conversations)
    commands.add('!export', 'P1: cid, export conversation', export_conversation)
    commands.add('!export_all', 'export all conversations', export_all_conversations)
    commands.add('!delete', 'P1: sid. Delete conversation with sid or current conversation', delete_conversation)
    commands.add('!delete_all', 'Delete all conversations', delete_all_conversations)
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
    try:
        while True:
            print(f'{C.OKBLUE + C.BOLD}You: {C.ENDC}')

            prompt = get_input(session=session, completer=completer)
            if commands.handle(prompt):
                print()
                continue

            print()
            print(f'{C.OKGREEN + C.BOLD}ChatGPT: {C.ENDC}')

            ask(chatbot, prompt)

            print()
    except (KeyboardInterrupt, EOFError):
        exit()
    except Exception as exc:
        error = CLIError('command line program unknown error')
        raise error from exc


@try_chatbot
def ask(chatbot: Chatbot, prompt):
    with Live(auto_refresh=False, vertical_overflow='visible') as live:
        for data in chatbot.ask(prompt, auto_continue=True):
            live.update(Markdown(data['message']), refresh=True)
    save.set('conversation_id', chatbot.conversation_id)
    save.save()

    cache = get_conversation_cache(chatbot)
    if cache.get_index(chatbot.conversation_id) == -1:
        conversation = {
            'id': chatbot.conversation_id,
            'title': 'New chat'
        }
        cache.add(conversation)


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
{C.OKGREEN}ChatGPT Command Tool{C.ENDC} (https://chat.openai.com/chat)

{C.OKCYAN}!help{C.ENDC}       Show All Commands
{C.OKCYAN}Esc, Enter{C.ENDC}  Send message / Execute command
{C.OKCYAN}Alt+Enter{C.ENDC}   Send message / Execute command
'''

if __name__ == '__main__':
    config = load_cmd_config()

    print(WELCOME_MESSAGE)

    
    print(f'Model: {C.WARNING}{config["model"]}{C.ENDC}')
    print()

    main(config)
