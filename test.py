import sys
import time
import os
from rich.console import Console
from parsbyte import print_hex_info

def clear_screen():
    print("\033[H", end="")

def print_header_info(data):

    if len(data) < 13:
        print("Ошибка: заголовок не найдет, мб файл короткий или не гифка")
        return 0, 0, 0, 0
    
    print("инфо о гифке")

    signature = data[:3].decode('ascii', errors='ignore')
    version = data[3:6].decode('ascii', errors='ignore')
    
    width = int.from_bytes(data[6:8], "little")
    height = int.from_bytes(data[8:10], "little")
    packed = data[10]
    bg_color_index = data[11]
    
    global_palette_flag = (packed & 0b10000000) != 0
    color_res = ((packed & 0b01110000) >> 4) + 1
    size_exp = (packed & 0b00000111)

    print(f"Тип: {signature}")
    print(f"Версия: {version}")
    print(f"Размер холста: {width}x{height} px")
    print(f"Глобальная палитра: {'Да' if global_palette_flag else 'Нет'}")

    if global_palette_flag:
        print(f"Размер г. палитры: {2**(size_exp+1)} цветов")

    print(f"Индекс цвета фона: {bg_color_index}")
    print(f"Разрешение цвета: {color_res} бит")
    
    return width, height, packed, bg_color_index

def lzw_decode(min_code_size, data):
    if not data:
        return []

    code_size = min_code_size + 1
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    next_code = end_code + 1
    mask = (1 << code_size) - 1
    
    dictionary = {i: [i] for i in range(clear_code)}
    
    bit_buffer = 0
    bit_len = 0
    idx = 0
    output = []
    
    code = 0
    old_code = None

    try:
        while idx < len(data) or bit_len >= code_size:
            while bit_len < code_size and idx < len(data):
                bit_buffer |= data[idx] << bit_len
                bit_len += 8
                idx += 1
                
            code = bit_buffer & mask
            bit_buffer >>= code_size
            bit_len -= code_size
            
            if code == clear_code:
                code_size = min_code_size + 1
                mask = (1 << code_size) - 1
                next_code = end_code + 1
                dictionary = {i: [i] for i in range(clear_code)}
                old_code = None
                continue
                
            if code == end_code:
                break
                
            if old_code is None:
                if code in dictionary:
                    output.extend(dictionary[code])
                    old_code = code
                    continue
                else:
                    continue 
                
            if code in dictionary:
                entry = dictionary[code]
                output.extend(entry)
                new_entry = dictionary[old_code] + [entry[0]]
            else:
                if old_code in dictionary:
                    entry = dictionary[old_code] + [dictionary[old_code][0]]
                    output.extend(entry)
                    new_entry = entry
                else:
                    break
                
            if next_code < 4096:
                dictionary[next_code] = new_entry
                next_code += 1
                if next_code >= (1 << code_size) and code_size < 12:
                    code_size += 1
                    mask = (1 << code_size) - 1
                    
            old_code = code
    except Exception:
        pass
        
    return output

def render_canvas_to_console(console, canvas, width, height):
    term_width = console.width
    scale_x = 1
    scale_y = 1
    
    if term_width > 0 and width * 2 > term_width:
        scale_x = (width * 2) // term_width + 1
    
    if height > 40:
        scale_y = height // 40 + 1

    grey_1 = (120, 120, 120) 
    grey_2 = (180, 180, 180)

    output_lines = []
    
    for y in range(0, height, scale_y):
        line_str = ""
        for x in range(0, width, scale_x):
            pixel_val = canvas[y * width + x]
            
            if pixel_val is None:
                if ((x // scale_x) + (y // scale_y)) % 2 == 0:
                    r, g, b = grey_1
                else:
                    r, g, b = grey_2
                line_str += f"[on rgb({r},{g},{b})]  [/]"
            else:
                r, g, b = pixel_val
                line_str += f"[on rgb({r},{g},{b})]  [/]"
                
        output_lines.append(line_str)
    
    clear_screen()
    for line in output_lines:
        console.print(line)

def main():
    if len(sys.argv) < 2:
        print("Что бы использовать: python test.py <file.gif>")
        return
    else:
        file_name = sys.argv[1]

    if not os.path.exists(file_name):
        print("Такого файлика нет")
        return

    with open(file_name, "rb") as f:
        data = f.read()

    console = Console()
    
    canvas_w, canvas_h, packed, bg_idx = print_header_info(data)
    print_hex_info(file_name)
    if canvas_w == 0 or canvas_h == 0:
        return
    
    count_color = 2 ** ((packed & 0b00000111) + 1)
    offset = 13
    
    global_palette = []
    try:
        if (packed & 0b10000000):
            for i in range(count_color):
                r, g, b = data[offset], data[offset+1], data[offset+2]
                global_palette.append((r, g, b))
                offset += 3
        else:
            global_palette = [(i, i, i) for i in range(256)]
    except IndexError:
        print("Битая палитра")
        return

    input("Нажми Enter для старта анимации")
    os.system('cls' if os.name == 'nt' else 'clear')

    bg_color = None
    if bg_idx < len(global_palette):
        bg_color = global_palette[bg_idx]
    
    canvas = [bg_color] * (canvas_w * canvas_h)
    
    prev_canvas_buffer = list(canvas)

    transparency_index = None
    delay_time = 10
    disposal_method = 0
    
    current_offset = offset

    try:
        while current_offset < len(data):
            block_type = data[current_offset]
            
            if block_type == 0x3B:
                break
                
            if block_type == 0x21:
                if current_offset + 2 >= len(data): break
                label = data[current_offset + 1]
                
                if label == 0xF9:
                    cnt_size = data[current_offset + 2]
                    packed_field = data[current_offset + 3]
                    
                    disposal_method = (packed_field >> 2) & 0b00000111
                    transparency_flag = (packed_field & 1)
                    
                    delay_time = int.from_bytes(data[current_offset+4:current_offset+6], "little")
                    if delay_time == 0: delay_time = 5
                    
                    if transparency_flag:
                        transparency_index = data[current_offset + 6]
                    else:
                        transparency_index = None
                        
                    current_offset += 2 + cnt_size + 1 + 1
                    
                else:
                    current_offset += 2
                    while True:
                        if current_offset >= len(data): break
                        sub_len = data[current_offset]
                        current_offset += 1
                        if sub_len == 0: break
                        current_offset += sub_len

            elif block_type == 0x2C:
                if current_offset + 10 >= len(data): break

                img_left = int.from_bytes(data[current_offset+1:current_offset+3], "little")
                img_top = int.from_bytes(data[current_offset+3:current_offset+5], "little")
                img_w = int.from_bytes(data[current_offset+5:current_offset+7], "little")
                img_h = int.from_bytes(data[current_offset+7:current_offset+9], "little")
                img_packed = data[current_offset+9]
                
                local_ct_flag = (img_packed & 0x80) != 0
                current_offset += 10
                
                current_palette = global_palette
                
                if local_ct_flag:
                    bpp = (img_packed & 0x07) + 1
                    local_size = (2 ** bpp) * 3
                    
                    if current_offset + local_size > len(data): break

                    local_palette = []
                    for i in range(2**bpp):
                        r, g, b = data[current_offset+i*3], data[current_offset+i*3+1], data[current_offset+i*3+2]
                        local_palette.append((r, g, b))
                    current_palette = local_palette
                    current_offset += local_size
                
                if current_offset >= len(data): break
                lzw_min = data[current_offset]
                current_offset += 1
                
                compressed = bytearray()
                while True:
                    if current_offset >= len(data): break
                    blk_len = data[current_offset]
                    current_offset += 1
                    if blk_len == 0: break
                    
                    if current_offset + blk_len > len(data):
                        compressed += data[current_offset:]
                        current_offset = len(data)
                        break
                        
                    compressed += data[current_offset : current_offset+blk_len]
                    current_offset += blk_len
                
                delta_pixels = lzw_decode(lzw_min, compressed)
                
                if disposal_method == 3:
                    prev_canvas_buffer = list(canvas)
                
                p_idx = 0
                for y in range(img_top, img_top + img_h):
                    for x in range(img_left, img_left + img_w):
                        if p_idx < len(delta_pixels):
                            color_idx = delta_pixels[p_idx]
                            p_idx += 1
                            
                            if x < canvas_w and y < canvas_h:
                                if transparency_index is not None and color_idx == transparency_index:
                                    continue
                                else:
                                    if color_idx < len(current_palette):
                                        canvas[y * canvas_w + x] = current_palette[color_idx]
                                    else:
                                        canvas[y * canvas_w + x] = (0,0,0)

                render_canvas_to_console(console, canvas, canvas_w, canvas_h)
                
                time.sleep(delay_time / 100.0)

                if disposal_method == 2:
                    for y in range(img_top, img_top + img_h):
                        for x in range(img_left, img_left + img_w):
                            if x < canvas_w and y < canvas_h:
                                canvas[y * canvas_w + x] = bg_color
                                
                elif disposal_method == 3:
                    canvas = list(prev_canvas_buffer)
                
                transparency_index = None
                disposal_method = 0
                delay_time = 10

            else:
                print("Неизвестный блок, скип")
                break
                
    except KeyboardInterrupt:
        print("Остановлено")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()