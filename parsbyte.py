
def dump_block(offset, data, size, title):
    chunk = data[offset: offset + size]
    hex_bytes = " ".join(f"{b:02X}" for b in chunk)
    print(f"{title}")
    print(f"{hex_bytes}\n")

def print_hex_info(file_name):
    with open(file_name,"rb") as f:
        data = f.read()
        f.close()

    dump_block(0, data, 6, "GIF Header")
    dump_block(6, data, 7, "Logical Screen Descriptor")

    packed = data[10]

    count_color = 2 ** ((packed & 0b00000111) + 1)
    global_color_table_size = count_color * 3
    start_palette = 13

    if packed & 0b10000000:
        dump_block(13, data, global_color_table_size,
                f"Global Color Table")

    offset = start_palette + global_color_table_size


    while offset < len(data) and data[offset] != 0x3B:

        if data[offset] == 0x21:
            label = data[offset + 1]

            if label == 0xF9:
                dump_block(offset, data, 8, "Graphic Control Extension")
                offset += 8
            else:
                start = offset
                offset += 2
                while True:
                    sub_block_size = data[offset]
                    if sub_block_size == 0:
                        offset += 1
                        break
                    offset += 1 + sub_block_size
                dump_block(start, data, offset - start, "Extension Block")
                
        elif data[offset] == 0x2C:
            dump_block(offset, data, 10, "Image Descriptor")

            packed = data[offset + 9]
            local_color_table_flag = (packed & 0b10000000) >> 7

            local_color_table_size = 0
            
            if local_color_table_flag:
                count_color = 2 ** ((packed & 0b00000111) + 1)
                local_color_table_size = count_color * 3
                dump_block(offset + 10, data, local_color_table_size,
                    f"Local Color Table")
            

            lzw_offset = offset + 10 + local_color_table_size
            lzw_min_code_size = data[lzw_offset]
            print("Image Data (LZW)")

            start = lzw_offset + 1
            offset = start
            total = 0
            while True:
                size = data[offset]
                offset += 1
                if size == 0:
                    break
                offset += size

            dump_block(start, data, offset - start, f"LZW Data")
            
    print("end")
