import re
import json

content = """```json
{
  "tool_calls": [
    {
      "name": "list_directory",
      "arguments": {"path": "."}
    }
  ]
}
```"""

available_tools = ['list_directory', 'read_file', 'search']

print("Testing tool call parsing...")
print(f"Content:\n{content}\n")

# Try the first pattern
pattern = r'```json\s*\n?({[\s\S]*?})\s*\n?```'
matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
print(f'Matches found: {len(matches)}')

if matches:
    print(f'Match: {matches[0][:200]}...')
    try:
        data = json.loads(matches[0])
        print(f'Parsed JSON successfully!')
        print(f'Keys: {data.keys()}')
        
        if 'tool_calls' in data:
            print('✓ Has tool_calls key!')
            calls = data['tool_calls']
            print(f'✓ tool_calls is list: {isinstance(calls, list)}')
            
            for i, call in enumerate(calls):
                print(f'\nCall {i}:')
                print(f'  Type: {type(call)}')
                print(f'  Has name: {"name" in call}')
                print(f'  Has arguments: {"arguments" in call}')
                
                if 'name' in call:
                    tool_name = call['name']
                    print(f'  Tool name: {tool_name}')
                    print(f'  Tool name lower: {tool_name.lower()}')
                    print(f'  Available tools: {available_tools}')
                    print(f'  Match: {tool_name.lower() in [t.lower() for t in available_tools]}')
                    
                    if tool_name.lower() in [t.lower() for t in available_tools]:
                        print(f'  ✓ WOULD BE ADDED TO tool_calls!')
                    else:
                        print(f'  ✗ REJECTED - not in available tools')
                        
    except json.JSONDecodeError as e:
        print(f'✗ JSON parse error: {e}')
else:
    print('✗ No matches found!')
