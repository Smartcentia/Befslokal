import re

def fix_all(content):
    # 0. Tighten lists: remove blank lines BETWEEN list items
    lines = content.split('\n')
    tight_lines = []
    for i in range(len(lines)):
        line = lines[i]
        curr_strip = line.strip()
        if i > 1 and curr_strip.startswith(('- ', '* ')) and lines[i-1].strip() == '' and lines[i-2].strip().startswith(('- ', '* ')):
            tight_lines.pop() # Remove the blank line
        tight_lines.append(line)
    
    content = '\n'.join(tight_lines)
    
    # 1. Normalize newlines: max 1 blank line
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 2. Re-apply Surrounding Blank Lines
    lines = content.split('\n')
    fixed_lines = []
    in_fence = False
    
    for i in range(len(lines)):
        line = lines[i]
        curr_strip = line.strip()
        
        if curr_strip.startswith('```'):
            if not in_fence:
                if fixed_lines and fixed_lines[-1].strip() != '':
                    fixed_lines.append('')
                in_fence = True
            else:
                in_fence = False
            fixed_lines.append(line)
            continue
            
        if in_fence:
            fixed_lines.append(line)
            continue

        if curr_strip.startswith('#'):
            if fixed_lines and fixed_lines[-1].strip() != '':
                fixed_lines.append('')
            fixed_lines.append(line)
            continue

        if curr_strip.startswith(('- ', '* ')):
            # Start of list
            if fixed_lines and fixed_lines[-1].strip() != '' and not fixed_lines[-1].strip().startswith(('- ', '* ')):
                fixed_lines.append('')
            
            # Indent fix (4 -> 2)
            if line.startswith('    -'):
                fixed_lines.append('  ' + line.lstrip())
            elif line.startswith('    *'):
                fixed_lines.append('  ' + line.lstrip())
            else:
                fixed_lines.append(line)
            continue

        fixed_lines.append(line)

    # 3. Pass 2: ensure blank line AFTER certain elements
    final_lines = []
    for i in range(len(fixed_lines)):
        line = fixed_lines[i]
        final_lines.append(line)
        
        if i < len(fixed_lines) - 1:
            curr_strip = line.strip()
            next_strip = fixed_lines[i+1].strip()
            if next_strip == '': continue
            
            if curr_strip.startswith('#'):
                final_lines.append('')
            elif curr_strip.startswith('```'):
                final_lines.append('')
            elif curr_strip.startswith(('- ', '* ')) and not next_strip.startswith(('- ', '* ', '  ')):
                # List end
                final_lines.append('')

    result = '\n'.join(final_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result

with open('backend/app/config/SCHEMA.md', 'r') as f:
    content = f.read()

fixed = fix_all(content)

with open('backend/app/config/SCHEMA.md', 'w') as f:
    f.write(fixed)
