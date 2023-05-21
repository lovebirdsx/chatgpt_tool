import argparse

from app import get_language, load_config
from cache import Cache
from asker import Prompt, do_ask_for_large_file_cmd
from common import open_file

LANGUAGE = get_language()

TRUNK_PROMPT_FIRST = f'''The code I sent you is a part of a code file.
Please help me generate a summary. include the most unique and helpful points.
no need to include all the details. 300 words or less. Reply in {LANGUAGE}:'''

TRUNK_PROMPT_NEXT = f'''The following code is a follow-up to the code I sent you before,
Please help me generate a summary. include the most unique and helpful points.
no need to include all the details. 300 words or less. Reply in {LANGUAGE}:'''

SUMARIZE_MUTI_PROMPT = f'''The following content is a summary of different parts of the same code file.
Please summarize them with the most unique and helpful points, into a list of key points and takeaways.
Reply in {LANGUAGE}:'''

SUMARIZE_SINGLE_PROMPT = f'''The texts I send to you are all come form the same code file,
Summarize them with the most unique and helpful points,
into a list of key points and takeaways. Reply in {LANGUAGE}:'''

PROG_NAME = 'code_explainer'
DESC = 'Code explainer used to generate code explanations and assist code reading'

def create_prompt() -> Prompt:
    return Prompt(
        TRUNK_PROMPT_FIRST,
        TRUNK_PROMPT_NEXT,
        SUMARIZE_MUTI_PROMPT,
        SUMARIZE_SINGLE_PROMPT
    )

def create_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument('-t', '--test', action='store_true', help='whether it is in test mode')
    parser.add_argument('-c', '--cache', action='store_true', help='whether to use cache')
    parser.add_argument('-f', '--file', help='path of the code file')
    parser.add_argument('-cfg', '--config', help='path of the config file')
    return parser


def gen_explain_header(path: str) -> str:
    return f'# {path}\n\n[Open](file:///{path})\n'

def test() -> None:
    print('Test passed')

if __name__ == '__main__':
    parser = create_args_parser()
    args = parser.parse_args()

    if args.test:
        test()
        exit(0)

    if not args.file:
        print(parser.format_help())
        exit(0)
    
    cache = Cache(PROG_NAME)
    if args.cache:
        result = cache.read(args.file)
        if result:
            print(result)
            open_file(cache.get_cache_path(args.file))
            exit(0)

    prompt = create_prompt()
    if args.file:
        config = load_config(args.config)
        result = do_ask_for_large_file_cmd(args.file, prompt, config)
        if not result:
            exit(1)

        cache.write(args.file, gen_explain_header(args.file) + '\n' + result + '\n')
        open_file(cache.get_cache_path(args.file))
        exit(0)
