from oned.spanner import oned_list
from twod.spanner import twod_list
import random
def generate_unique_1d(n, low = -100, high = 100):
    return random.sample(range(low, high + 1), n)

def generate_unique_2d(n, low = -100, high = 100):
    points = set()
    while len(points) < n:
        x = random.randint(low, high)
        y = random.randint(low, high)
        points.add((x, y))
    return list(points)

def choose_num():
     while True:
        user_input1 = input("Enter a number for the number of random nodes: ")
        try:
            value = int(user_input1)
        except ValueError:
            print("Please enter a number")
            continue
        if value <= 0:
            print("Please enter a number greater than 0")
            continue
        return value
def main():

    while True:
        user_input = input("Enter 1 for 1D or 2 for 2D: ")
        if user_input == "1":
            oned_list(generate_unique_1d(choose_num()))
        elif user_input == "2":
            twod_list(generate_unique_2d(choose_num()))
        else:
            break

    print("program terminated")
if __name__ == "__main__":
    main()