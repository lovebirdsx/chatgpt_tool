import os

from revChatGPT.V1 import Chatbot
from common import get_next_ok_path, print_md, to_valid_filename, try_chatbot
from revChatGPT.typings import CLIError, C


class ConversationExporter:
    def __init__(self, root: str, chatboot: Chatbot) -> None:
        self.__root = root
        self.__chatbot = chatboot
        self.__conversations = [self.__filename_to_title(f) for f in os.listdir(self.__root) if os.path.isfile(os.path.join(self.__root, f))]

    @try_chatbot
    def __get_history(self, cid: str) -> dict:
        history = self.__chatbot.get_msg_history(cid, 'utf-8')
        return history # type: ignore

    def __save(self, cid: str, title: str, path: str) -> None:
        history = self.__get_history(cid)
        mapping = history['mapping'] # type: ignore
        messages = [msg['message'] for msg in mapping.values() if 'message' in msg and 'content' in msg['message']]

        try:
            with open(path, 'w', encoding='utf8') as f:
                f.write(f'# {title}\n\n')
                for msg in messages:
                    content_type = msg['content']['content_type']
                    if content_type != 'text':
                        continue
                    text = msg['content']['parts'][0]
                    if not text.strip():
                        continue

                    if msg['author']['role'] == 'assistant':
                        f.write(f'ChatGPT:\n{text}\n\n')
                    elif msg['author']['role'] == 'user':
                        f.write(f'You:\n{text}\n\n')
        except:
            raise CLIError(f'Failed to save conversation to: {path}')
    
    def export(self, cid: str, title: str, force: bool = True) -> str | None:
        path = self.__get_path(title)
        if os.path.exists(path):
            if not force:
                print(f'{C.WARNING}Conversation {title} already exists, ignored{C.ENDC}')
                return None
            else:
                print(f'{C.WARNING}Conversation {title} already exists, overwriting{C.ENDC}')

        self.__save(cid, to_valid_filename(title), path)
        return os.path.normpath(path)

    def delete(self, title: str) -> None:
        path = self.__get_path(title)
        if os.path.exists(path):
            os.remove(path)
    
    def rename(self, cid: str, old_title: str, new_title: str) -> None:
        old_path = self.__get_path(old_title)
        new_path = self.__get_path(new_title)

        if not os.path.exists(old_path):
            print(f'{C.WARNING}Old conversation {old_title} does not exist{C.ENDC}')
            self.__save(cid, new_title, new_path)
            return

        if os.path.exists(new_path):
            print(f'{C.WARNING}Conversation {new_title} already exists{C.ENDC}')
            ok_path = get_next_ok_path(new_path)
            print(f'{C.WARNING}Saving to {ok_path}{C.ENDC}')
            os.rename(old_path, ok_path)
            return

        os.rename(old_path, new_path)
    
    def __title_to_filename(self, title: str) -> str:
        return to_valid_filename(title) + '.md'
    
    def __filename_to_title(self, filename: str) -> str:
        return os.path.splitext(os.path.basename(filename))[0]

    def __get_path(self, title: str) -> str:
        return os.path.join(self.__root, self.__title_to_filename(title))
    
    @property
    def all_titles(self) -> list[str]:
        return [os.path.splitext(os.path.basename(f))[0] for f in self.__conversations]
    
    def has_conversation(self, title: str) -> bool:
        return title in self.__conversations

    def print_conversation(self, titile: str) -> None:
        path = self.__get_path(titile)
        if path is None:
            print(f'{C.WARNING}Conversation {titile} not found{C.ENDC}')
        else:
            with open(path, 'r', encoding='utf8') as f:
                print_md(f.read())
        print()
