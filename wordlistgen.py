import random
import string

# Get the number of SSIDs to generate from the user
while True:
    try:
        num_ssids = int(input("Enter the number of SSIDs to generate: "))
        if num_ssids <= 0:
            print("Please enter a positive number.")
        else:
            break
    except ValueError:
        print("Invalid input. Please enter a valid number.")

# Define parameters for the SSID lengths
min_length = 6   # Minimum length of SSIDs
max_length = 12  # Maximum length of SSIDs

# Generate random SSIDs
def generate_ssid(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Create the wordlist
output_file = (input("What would you like to name your wordlist file?: "))

with open(output_file, "w") as f:
    for _ in range(num_ssids):
        ssid_length = random.randint(min_length, max_length)
        ssid = generate_ssid(ssid_length)
        f.write(ssid + "\n")

print(f"Wordlist with {num_ssids} SSIDs generated as '{output_file}'.")
