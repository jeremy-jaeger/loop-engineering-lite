# Test Stack implementation

class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        if not isinstance(item, int) or isinstance(item, bool):
            raise TypeError(f"Expected an integer or boolean, got {type(item)}")
        self.items.append(item)
    
    def pop(self):
        if not self.items:
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        if not self.items:
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def __len__(self):
        return len(self.items)


def test_push():
    stack = Stack()
    stack.push(1)
    assert stack == [1], f"Expected [1], got {stack}"

def test_pop():
    stack = Stack()
    stack.push(1)
    popped = stack.pop()
    assert popped == 1, f"Expected 1, got {popped}"

def test_peek():
    stack = Stack()
    stack.push(1)
    peeked = stack.peek()
    assert peeked == 1, f"Expected 1, got {peeked}"

def test_empty_stack_pop_raises_index_error():
    stack = Stack()
    try:
        stack.pop()
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

def test_empty_stack_push_raises_index_error():
    stack = Stack()
    try:
        stack.push(1)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass