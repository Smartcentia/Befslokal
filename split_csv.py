import os

input_file = '/Users/frank/Documents/BEFS_CLEAN/Eiendomfebruar.csv'
with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

header = lines[0]
data_lines = lines[1:]

total_lines = len(data_lines)
part_size = total_lines // 3

part1 = data_lines[:part_size]
part2 = data_lines[part_size:2*part_size]
part3 = data_lines[2*part_size:]

def write_part(filename, h, data):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(h)
        f.writelines(data)

write_part('/Users/frank/Documents/BEFS_CLEAN/Eiendomfebruar_part1.csv', header, part1)
write_part('/Users/frank/Documents/BEFS_CLEAN/Eiendomfebruar_part2.csv', header, part2)
write_part('/Users/frank/Documents/BEFS_CLEAN/Eiendomfebruar_part3.csv', header, part3)

print(f"Total data lines: {total_lines}")
print(f"Part 1: {len(part1)} lines")
print(f"Part 2: {len(part2)} lines")
print(f"Part 3: {len(part3)} lines")
print("Done splitting into 3 files.")
