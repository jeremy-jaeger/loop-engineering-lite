# Stack Implementation

class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """Push an item onto the stack."""
        self.items.append(item)
    
    def pop(self):
        """Pop and return the last item from the stack."""
        if not self.items:
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        """Return the top item without removing it."""
        if not self.items:
            raise IndexError("Stack is empty")
        return self.items[-1]

# Test Stack implementation

def test_push():
    stack = []
    stack.push(1)
    assert stack == [1], f"Expected [1], got {stack}"

def test_pop():
    stack = [1, 2, 3]
    popped = stack.pop()
    assert popped == 3, f"Expected 3, got {popped}"

def test_peek():
    stack = [1, 2, 3]
    peeked = stack.peek()
    assert peeked == 3, f"Expected 3, got {peeked}"

def test_empty_stack_pop_raises_index_error():
    stack = []
    try:
        stack.pop()
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

def test_empty_stack_push_raises_index_error():
    stack = []
    try:
        stack.push(1)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass