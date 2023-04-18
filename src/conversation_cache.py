class ConversationCache:

    def __init__(self, conversations: list[dict]) -> None:
        self.conversations = conversations

    def exist(self, index: int) -> bool:
        return 0 <= index and index < len(self.conversations)
    
    def get_id(self, index: int) -> str:
        return self.conversations[index].get('id')
    
    def delete(self, index: int):
        if not self.exist(index):
            return
        del self.conversations[index]
    
    def add(self, conversation: dict):
        self.conversations.insert(0, conversation)

    def get_title(self, index: int) -> str:
        return self.conversations[index].get('title')

    def get_index(self, conversation_id: str) -> int:
        for i, conv in enumerate(self.conversations):
            if conv.get('id') == conversation_id:
                return i
        return -1
    
    def titles(self) -> list[str]:
        return [conv.get('title') for conv in self.conversations]
    
    def __getitem__(self, index: int) -> dict | None:
        if index < 0 or index >= len(self.conversations):
            return None
        return self.conversations[index]
        
    def __len__(self) -> int:
        return len(self.conversations)
