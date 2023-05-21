import argparse
import os
from git.repo import Repo
from app import get_language, get_save_path, load_config
from asker import Prompt, do_ask_for_large_file_cmd
from common import open_file, write_file

LANGUAGE = get_language()

TRUNK_PROMPT_FIRST = f'''The content I sent you is a part of a code patch.
please help me do a brief code review. If any bug risk and improvement suggestion are welcome.
Reply in {LANGUAGE}:'''

TRUNK_PROMPT_NEXT = f'''Please continue to do code view.
If any bug risk and improvement suggestion are welcome. Reply in {LANGUAGE}:'''

SUMARIZE_MUTI_PROMPT = f'''The following content is code reviews of different parts of the same code patch.
First, please summarize them with the most unique and helpful points, into a list of key points and takeaways.
Then, please provide a commit message 30 words or less. Please reply in {LANGUAGE}:'''

SUMARIZE_SINGLE_PROMPT = f'''Bellow is the code patch, First, please help me do a brief code review,
If any bug risk and improvement suggestion are welcome. 
Then, please provide a commit message 30 words or less.
Please reply in {LANGUAGE}:'''

PROG_NAME = 'code_reviewer'
DESC = '''A code reviewer used to generate code review

* Generate the latest (or unsubmitted) review based on the git repository where the incoming file is located
* Generate the submission information of this review
'''

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
    parser.add_argument('-f', '--file', help='file path, the git repository root directory will be taken as this file directory')
    parser.add_argument('-cfg', '--config', help='path of the config file')

    return parser

def gen_patch(repo: Repo, file) -> str:
    if not repo:
        raise Exception(f'The directory where the file [{file}] is located is not a git repository')
    
    repo_name = os.path.basename(repo.working_dir)
    patch_path = os.path.join(get_save_path(), f'{repo_name}.patch')
    if repo.is_dirty():
        repo.git.add(A=True)
        repo.index.commit('Automatically submitted by code_reviewer')
        os.system(f'cd {os.path.dirname(file)} && git format-patch -1 --stdout > {patch_path}')
        repo.git.reset('HEAD~1')
    else:
        os.system(f'cd {os.path.dirname(file)} && git format-patch -1 --stdout > {patch_path}')

    if not os.path.exists(patch_path):
        raise Exception(f'Failed to generate patch file. Please check whether the directory where the file [{file}] is located is a git repository')
    return patch_path

def gen_review_header(repo: Repo) -> str:
    commit_message = repo.head.commit.message.strip()
    return f'''# Code review

Repository: {os.path.basename(repo.working_dir)}
Branch: {repo.active_branch.name}
Commit information: {"(unsubmitted)" if repo.is_dirty() else commit_message}
Commit author: {"(unknown)" if repo.is_dirty() else repo.head.commit.author}
'''
    

def test() -> None:
    repo = Repo(os.path.dirname(__file__), search_parent_directories=True)
    print(gen_review_header(repo))


if __name__ == '__main__':
    parser = create_args_parser()
    args = parser.parse_args()

    if args.test:
        test()
        exit(0)

    file = args.file
    if not file:
        print(parser.format_help())
        exit(0)

    repo = Repo(os.path.dirname(file), search_parent_directories=True)
    patch_path = gen_patch(repo, file)
    print(f'Generated patch file [{patch_path}]')

    prompt = create_prompt()
    config = load_config(args.config)
    result = do_ask_for_large_file_cmd(patch_path, prompt, config)
    
    review_header = gen_review_header(repo)
    repo_name = os.path.basename(repo.working_dir)
    result_path = os.path.normpath(os.path.join(get_save_path(), f'code_reviewer/{repo_name}.md'))
    write_file(result_path, review_header + '\n' + result + '\n')
    print(f'Results saved in: {result_path}')
    open_file(result_path)
