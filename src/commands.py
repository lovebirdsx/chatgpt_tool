from typing import Callable

from revChatGPT.typings import Colors

C = Colors()

class CommandItem:
    def __init__(self, name: str, help: str, func: Callable[..., object]):
        self.name = name
        self.help = help
        self.func = func


class Commands:
    def __init__(self):
        self.commands = []
        self.add('.help', 'Show this message', lambda _: print(self.get_help()))

    def add(self, name: str, help: str, func: Callable[..., object]):
        self.commands.append(CommandItem(name, help, func))

    def get_help(self) -> str:
        return '\n'.join([f'{C.OKCYAN}{item.name:<20}{C.ENDC}{item.help}' for item in self.commands])

    def get_names(self) -> list[str]:
        return [item.name for item in self.commands]

    def handle(self, command: str) -> bool:
        command = command.strip()
        if command.startswith('.'):
            command = command.lower()

        args = command.split(' ')
        command_name = args[0]
        for item in self.commands:
            if item.name == command_name:
                item.func(args)
                return True
        return False