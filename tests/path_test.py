prefix = ["!!!!", "!!!", "!!", "!", ""]
BASE87 = "#$&()*+,-/0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_`abcdefghijklmnopqrstuvwxyz{|}~"
charNum = ""
i = 0
number = 86
while number >= 86:
    div, mod = divmod(number, 86)
    charNum = BASE87[mod] + charNum
    number = int(div)
    i += 1
charNum = prefix[i] + BASE87[number] + charNum
print (charNum)
