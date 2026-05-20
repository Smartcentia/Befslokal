import sys

with open('backend/app/config/SCHEMA.md', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    # MD022: Headings should be surrounded by blank lines
    if line.startswith('#'):
        if i > 0 and lines[i-1].strip() != '':
            print(f'MD022 Above Error at line {i+1}: {line.strip()}')
        if i < len(lines) - 1 and lines[i+1].strip() != '':
            print(f'MD022 Below Error at line {i+1}: {line.strip()}')

    # MD031: Fenced code blocks should be surrounded by blank lines
    if line.strip().startswith('```'):
        is_end = False
        # Simple heuristic: if we were in a fence, this is the end.
        # But let's just use a state variable.
        pass

in_fence = False
for i, line in enumerate(lines):
    if line.strip().startswith('```'):
        if not in_fence:
            # Start of fence
            if i > 0 and lines[i-1].strip() != '' and not lines[i-1].strip().startswith('#'):
                print(f'MD031 Above Error at line {i+1}: {line.strip()}')
            in_fence = True
        else:
            # End of fence
            if i < len(lines) - 1 and lines[i+1].strip() != '':
                print(f'MD031 Below Error at line {i+1}: {line.strip()}')
            in_fence = False

    # MD012: Multiple blank lines
    if i > 0 and line.strip() == '' and lines[i-1].strip() == '':
        print(f'MD012 Error at line {i+1}')

    # MD032: Lists should be surrounded by blank lines
    if (line.lstrip().startswith('- ') or line.lstrip().startswith('* ')) and not line.startswith(' '):
         if i > 0 and lines[i-1].strip() != '' and not lines[i-1].strip().startswith(('- ', '* ', '#')):
            print(f'MD032 Above Error at line {i+1}: {line.strip()}')
         if i < len(lines) - 1 and lines[i+1].strip() != '' and not lines[i+1].strip().startswith(('- ', '* ', '#', '  ')):
            print(f'MD032 Below Error at line {i+1}: {line.strip()}')

    # MD007: Unordered list indentation
    # Check if a list item is indented by anything other than 0 or 2 spaces
    if line.strip().startswith(('- ', '* ')):
        indent = len(line) - len(line.lstrip())
        if indent % 2 != 0:
            print(f'MD007 Non-2-space indent Error at line {i+1}: {indent} spaces')
