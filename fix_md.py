import re

def fix_markdown(content):
    # Rule 4: No more than one consecutive blank line
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    lines = content.split('\n')
    new_lines = []
    
    in_fence = False
    
    for i, line in enumerate(lines):
        # Rule 1 & 5 & 2: Heading, Fence, List
        
        is_heading = line.strip().startswith('#')
        is_fence = line.strip().startswith('```')
        is_list = line.strip().startswith(('- ', '* ')) and not line.startswith(' ')
        
        if is_fence:
            if not in_fence: # Start of fence
                if new_lines and new_lines[-1].strip() != '':
                    new_lines.append('')
                new_lines.append(line)
                in_fence = True
            else: # End of fence
                new_lines.append(line)
                in_fence = False
                # We'll add a blank line after if the NEXT line isn't blank
                # But we can't look ahead easily here without a second pass or check
            continue

        if in_fence:
            new_lines.append(line)
            continue

        if is_heading:
            if new_lines and new_lines[-1].strip() != '':
                new_lines.append('')
            new_lines.append(line)
            if i < len(lines) - 1 and lines[i+1].strip() != '':
                new_lines.append('')
            continue

        if is_list:
            if new_lines and new_lines[-1].strip() != '' and not new_lines[-1].strip().startswith(('- ', '* ')):
                new_lines.append('')
            
            # Rule 3: Nested list items are indented by 2 spaces.
            # (Wait, this is for top level. Sublevels are handled differently)
            new_lines.append(line)
            continue
            
        # Handle indent for sub-lists
        if line.lstrip().startswith(('- ', '* ')) and line.startswith(' '):
            # Find indent
            indent = len(line) - len(line.lstrip())
            # If sub-level (usually parent is at 0, next is at 2, 4...)
            # User says "Nested list items are indented by 2 spaces"
            # This usually means parent is 0, first nesting is 2.
            # Current file has 2 spaces mostly. If it was 4, fix to 2.
            if indent == 4:
                new_lines.append('  ' + line.lstrip())
            else:
                new_lines.append(line)
            continue

        # For normal text, if previous was a list and this is text, add blank line
        if new_lines and new_lines[-1].strip().startswith(('- ', '* ')) and line.strip() != '' and not line.strip().startswith(('- ', '* ')):
            new_lines.append('')
            
        new_lines.append(line)

    # Post-process for blank line after fence/list/heading
    final_lines = []
    for i, line in enumerate(new_lines):
        final_lines.append(line)
        if line.strip().startswith('```') and i > 0:
            # If this was end of fence
            # (Simple check: we don't track state here, but we can)
            pass 
            
    # Actually it's easier to just do multiple passes with regex
    return '\n'.join(new_lines)

def fix_all(content):
    # Rule 4: Normalize newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Rule 5: Blank lines around fences
    content = re.sub(r'([^\n])\n(```)', r'\1\n\n\2', content)
    content = re.sub(r'(```)\n([^\n])', r'\1\n\n\2', content)
    
    # Rule 1: Blank lines around headings
    content = re.sub(r'([^\n])\n(#)', r'\1\n\n\2', content)
    content = re.sub(r'(#+ [^\n]+)\n([^\n\s])', r'\1\n\n\2', content)
    
    # Rule 2: Blank lines around lists
    # List start
    content = re.sub(r'([^\n\s#])\n([-*] )', r'\1\n\n\2', content)
    # List end
    # (Matches line ending in list item followed by non-list line)
    def list_end_fix(m):
        if m.group(2).startswith(('#', '```')): return m.group(0)
        return m.group(1) + '\n\n' + m.group(2)
    
    # complex regex for list end to avoid breaking nested lists
    # But let's keep it simple: if line starts with '-' and next line doesn't start with ' ' or '-', add blank line.
    lines = content.split('\n')
    fixed_lines = []
    for i in range(len(lines)):
        fixed_lines.append(lines[i])
        if i < len(lines) - 1:
            curr = lines[i].strip()
            nxt = lines[i+1].strip()
            if curr.startswith(('- ', '* ')) and nxt != '' and not nxt.startswith(('- ', '* ', '  ')):
                fixed_lines.append('')
            elif nxt.startswith(('- ', '* ')) and curr != '' and not curr.startswith(('- ', '* ', '#', '```')):
                fixed_lines.append('')
    
    content = '\n'.join(fixed_lines)
    
    # Rule 3: Nested list indentation fix (4 -> 2)
    content = re.sub(r'\n    ([-*] )', r'\n  \1', content)
    
    # Final cleanup of multiple blanks again
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

with open('backend/app/config/SCHEMA.md', 'r') as f:
    content = f.read()

fixed = fix_all(content)

with open('backend/app/config/SCHEMA.md', 'w') as f:
    f.write(fixed)
