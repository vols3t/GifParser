

with open("pepapig-sigma.gif","rb") as f:
    data = f.read()
    f.close()

header = data[:6].decode("ascii")
wh = int.from_bytes(data[6:8], "little")
ht = int.from_bytes(data[8:10], "little")

print(header, wh, ht)
