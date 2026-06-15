import random

score=0

while True:
    r=random.randint(0,7)
    c=random.randint(0,7)

    for i in range(8):
        print("+----"*8+"+")
        for j in range(8):
            if i==r and j==c:
                print("|#(b)" if (i+j)%2==0 else "|#(w)",end="")
            else:
                print("|----" if (i+j)%2==0 else "|    ",end="")
        print("|")
    print("+----"*8+"+")

    s=input("\nGuess the square (e.g. e4): ").lower()

    file=chr(ord('a')+c)
    rank=8-r

    if s==file+str(rank):
        score+=1
        print("Correct. Score =",score)
    else:
        print("Wrong.")
        print(f"Correct square was: {file}{rank} ({'Black' if (r+c)%2==0 else 'White'})")
        break

print("\nGame Over")
print("Final Score:",score)