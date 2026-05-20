import re

def fix_all(content):
    # Rule 4: Normalize newlines (max 1 blank line)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    lines = content.split('\n')
    fixed_lines = []
    
    in_fence = False
    
    for i in range(len(lines)):
        line = lines[i]
        curr_stripped = line.strip()
        
        if curr_stripped.startswith('```'):
            if not in_fence: # Start of fence
                # Rule 5: Blank line before fence
                if fixed_lines and fixed_lines[-1].strip() != '':
                    fixed_lines.append('')
                in_fence = True
            else: # End of fence
                in_fence = False
                # We'll add a blank line after later
            fixed_lines.append(line)
            continue
            
        if in_fence:
            fixed_lines.append(line)
            continue

        # Rule 1: Headings
        if curr_stripped.startswith('#'):
            if fixed_lines and fixed_lines[-1].strip() != '':
                fixed_lines.append('')
            fixed_lines.append(line)
            # We'll ensure blank line after later
            continue

        # Rule 2: List (Surrounded, not between items)
        is_list_item = curr_stripped.startswith(('- ', '* '))
        
        if is_list_item:
            # If start of a new list (previous line was not a list item and not blank)
            if fixed_lines and fixed_lines[-1].strip() != '' and not fixed_lines[-1].strip().startswith(('- ', '* ')):
                fixed_lines.append('')
            
            # Rule 3: Nested list items are indented by 2 spaces.
            # If it's a sub-item (indented)
            if line.startswith(' '):
                indent = len(line) - len(line.lstrip())
                # If it's indented by 4, change to 2
                if indent == 4:
                    fixed_lines.append('  ' + line.lstrip())
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            continue

        # Normal text or other
        fixed_lines.append(line)

    # Second pass: ensure blank line after headings, lists, fences
    final_lines = []
    for i in range(len(fixed_lines)):
        line = fixed_lines[i]
        final_lines.append(line)
        
        if i < len(fixed_lines) - 1:
            curr_strip = line.strip()
            next_strip = fixed_lines[i+1].strip()
            
            # If next line is already blank, skip
            if next_strip == '': continue
            
            # After Heading
            if curr_strip.startswith('#'):
                final_lines.append('')
            # After End of Fence
            elif curr_strip.startswith('```'):
                final_lines.append('')
            # After List (if next is not a list item)
            elif curr_strip.startswith(('- ', '* ')) and not next_strip.startswith(('- ', '* ')):
                final_lines.append('')
    
    # Final cleanup: rule 4 again
    result = '\n'.join(final_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result

with open('backend/app/config/SCHEMA.md', 'r') as f:
    content = f.read()

fixed = fix_all(content)

with open('backend/app/config/SCHEMA.md', 'w') as f:
    f.write(fixed)
