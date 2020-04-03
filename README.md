Just a homebrewed state machine JSON parser.

Why?

Because I wanted to have better visibility into why a JSON parse was failing...

Implemented using recursive functions cause it's easier, so there's a corresponding object/array depth limit dictated by the call stack.
