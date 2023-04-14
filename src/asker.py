import time
import tiktoken

from revChatGPT.V1 import Chatbot, configure

TRUNK_TOKEN_SIZE = 2800
TRUNK_STR_SIZE = 11500
MAX_ASK_RETRY_COUNT = 10

class AskTimeoutException(Exception):
    pass

def get_next_trunk_text(encoder: tiktoken.Encoding, tockens: list[int], tocken_index: int) -> tuple[str, int]:
    chunk_token_size = TRUNK_TOKEN_SIZE
    chunk_str = ''
    for _ in range(0, 20):
        chunk_tockens = tockens[tocken_index : tocken_index + chunk_token_size]
        chunk_str = encoder.decode(chunk_tockens)
        if len(chunk_str) > TRUNK_STR_SIZE:
            chunk_token_size = int(chunk_token_size * 0.9)
        else:
            return chunk_str, tocken_index + chunk_token_size
    raise Exception('无法生成下一个trunk')

def split_code(gpt_mode: str, code: str) -> tuple[list[str], int]:
    encoder = tiktoken.encoding_for_model(gpt_mode)
    tockens = encoder.encode(code)
    result = []
    tocken_index = 0
    while True:
        chunk_str, next_tocken_index = get_next_trunk_text(encoder, tockens, tocken_index)
        result.append(chunk_str)
        # print(f'Chunk str length: {len(chunk_str)} token_count: {next_tocken_index - tocken_index}')
        if next_tocken_index >= len(tockens):
            break
        tocken_index = next_tocken_index
    
    return result, len(tockens)

def ask_trunk_impl(bot: Chatbot, prompt_prefix: str, trunk: str, log_prefix = '') -> str:
    print(f'{log_prefix}提问: {prompt_prefix} 文本长度: {len(trunk)}\n')
    prev_text = ''
    for data in bot.ask(prompt_prefix + trunk):
        message = data["message"][len(prev_text) :]
        print(message, end="", flush=True)
        prev_text = data["message"]
    
    print('\n-----------------------------------------------------------------')
    return prev_text

def ask(bot: Chatbot, prompt_prefix: str, code: str, log_prefix = '') -> str:
    for i in range(0, MAX_ASK_RETRY_COUNT):
        try:
            return ask_trunk_impl(bot, prompt_prefix, code, log_prefix)
        except Exception as e:
            print(f'错误:{e}')
            print(f'\n[{i+1}/{MAX_ASK_RETRY_COUNT}]3秒后重试')
            time.sleep(3)
    raise AskTimeoutException(f'重试次数超过上限{MAX_ASK_RETRY_COUNT}')

class Prompt:
    def __init__(self, trunk_first, trunk_next, sumarize_muti, sumarize_single) -> None:
        self.trunk_first = trunk_first
        self.trunk_next = trunk_next
        self.sumarize_muti = sumarize_muti
        self.sumarize_single = sumarize_single

def ask_for_content(bot: Chatbot, content: str, prompt: Prompt) -> list[str]:
    trunks, token_count = split_code(bot.config['model'], content)
    print(f'Code length: {len(content)} token_count: {token_count} trunks: {len(trunks)}')
    result = []
    if len(trunks) > 1:
        texts = []
        i = 0
        for trunk in trunks:
            i += 1
            prompt0 = prompt.trunk_first if i == 1 else prompt.trunk_next
            trunk_response = ask(bot, prompt0, trunk, f'[{i}/{len(trunks)}] ')
            texts.append(trunk_response)
            result.append( trunk_response)

        final_response = ask(bot, prompt.sumarize_muti, '\n'.join(texts))
        result.append(final_response)
    else:
        result.append(ask(bot, prompt.sumarize_single, content))
    
    return result

def format_result(result: list[str]) -> str:
    formated_result = []
    for i, r in enumerate(result):
        if i > 0:
            formated_result.append(f'')

        if i < len(result) - 1:
            formated_result.append(f'## ChatGPT [{i+1}/{len(result) - 1}]\n\n{r}')
        else:
            formated_result.append(f'## ChatGPT汇总:\n\n{r}')
    return '\n'.join(formated_result)


def do_ask_for_large_file_cmd(path: str, prompt: Prompt) -> str:
    with open(path, 'r') as f:
        code = f.read()
        conf = configure()
        # print(conf)
        bot = Chatbot(conf)
        result = ask_for_content(bot, code, prompt)

        for i in range(0, MAX_ASK_RETRY_COUNT):
            try:
                bot.delete_conversation(bot.conversation_id)
                break
            except Exception as e:
                print(f'错误:{e}')
                print(f'\n[{i+1}/{MAX_ASK_RETRY_COUNT}]删除会话失败，3秒后重试')
                time.sleep(3)

        return format_result(result)


def test_split_code():
    path = 'D:\\Aki\\Source\\Client\\TypeScript\\Src\\Core\\Net\\Net.ts'
    with open(path, 'r') as f:
        code = f.read()
        trunks, token_count = split_code('gpt-3.5-turbo', code)
        print(f'Code length: {len(code)} token_count: {token_count} trunks: {len(trunks)}')

def test():
    test_split_code()

if __name__ == '__main__':
    test()
