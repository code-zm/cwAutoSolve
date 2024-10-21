import time
import re
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def read_configs(filename):
    # Reads key-value configurations from a given file
    configs = {}
    with open(filename, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                configs[key.strip()] = value.strip().strip('"')
    return configs

def login(driver, username, password):
    # Logs in to the Codewars website
    driver.get("https://www.codewars.com/users/sign_in")

    # Wait for the username field to be present and enter the username
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "user_email"))
    )
    password_field = driver.find_element(By.ID, "user_password")

    # Enter username and password
    username_field.send_keys(username)
    password_field.send_keys(password)

    # Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    login_button.click()

    # Wait for the train button to be clickable and click it
    train_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "personal-trainer-play"))
    )
    train_button.click()
    print("Train button clicked after login.")

def cleanResponse(responseText):
    # Cleans the AI response by removing code block markers and the word 'python'
    cleaned_text = re.sub(r"```python\n|```", "", responseText, flags=re.DOTALL).strip()
    return cleaned_text

def getCodeFeedback(apiKey, gptInput):
    # Gets code feedback from the OpenAI API
    client = openai.OpenAI(api_key=api_key)
    prompt = f"Complete the following coding challenge, only output the required code and nothing else. Output should only be the markdown text for me to copy. DO NOT INCLUDE ANY TEST CASES IN YOUR OUTPUT.\n\n{gptInput}"
    
    try:
        # Send the prompt to the OpenAI API and receive a response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional python programmer. You do not communicate in your responses, you simply output code."},
                {"role": "user", "content": prompt}
            ]
        )
        responseText = response.choices[0].message.content
        print("Feedback Received:\n")
        print(responseText)
        return responseText
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def aiDebugger(api_key, problem_description, ai_written_code, failed_outputs, error_log):
    # Debugs the given code using OpenAI API
    client = openai.OpenAI(api_key=api_key)
    prompt = f"""Debug the following code based on the provided problem description, failed outputs, and error log.
Problem Description:
{problem_description}

AI Written Code:
{ai_written_code}

Failed Outputs:
{failed_outputs}

Error Log:
{error_log}

Please provide the corrected code.
DO NOT INCLUDE ANY TEST CASES IN YOUR OUTPUT
"""
    try:
        # Send the debug request to the OpenAI API and receive the debugged code
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional python programmer. You do not communicate in your responses, you simply output code."},
                {"role": "user", "content": prompt}
            ]
        )
        debugged_code = response.choices[0].message.content
        return debugged_code
    except Exception as e:
        print(f"An error occurred while debugging: {e}")
        return None

def solve_challenge(driver, api_key, problem_counter):
    # Solves a single coding challenge by interacting with the Codewars page and the OpenAI API
    try:
        print("Waiting for description element.")
        # Wait until the challenge description element is present
        description_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "description"))
        )
        description_text = description_element.text
        print("Description text extracted.")

        # Wait for the CodeMirror editor to be present
        code_mirror = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
        )
        # Extract starter code from the CodeMirror editor
        starter_code = driver.execute_script("return arguments[0].CodeMirror.getValue();", code_mirror)
        print("Starter code extracted.")

        # Wait for the fixture element to be present and extract sample tests
        fixture_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "fixture"))
        )
        fixture_code_mirror = fixture_element.find_element(By.CLASS_NAME, "CodeMirror")
        sample_tests = driver.execute_script("return arguments[0].CodeMirror.getValue();", fixture_code_mirror)
        print("Sample tests extracted.")

        # Get code feedback from the OpenAI API
        ai_response = getCodeFeedback(api_key, f"Description: {description_text}\n\nStarter Code:\n{starter_code}\n\nSample Tests:\n{sample_tests}\n\nPlease complete the code.")
        print("AI response received.")
        cleaned_response = cleanResponse(ai_response)

        # Clear the CodeMirror editor and paste the cleaned AI response
        driver.execute_script("arguments[0].CodeMirror.setValue('');", code_mirror)
        driver.execute_script("arguments[0].CodeMirror.setValue(arguments[1]);", code_mirror, cleaned_response)
        print("Cleaned response pasted into the editor.")

        # Click the attempt button to test the code
        attempt_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "attempt_btn"))
        )
        driver.execute_script("arguments[0].click();", attempt_button)
        print("Attempt button clicked.")
        time.sleep(10)

        # Switch to the iframe containing the test results
        iframe = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "runner_frame"))
        )
        driver.switch_to.frame(iframe)
        print("Switched to runner iframe.")

        # Wait for the result summary to be present and retrieve it
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2"))
        )
        result_element = driver.find_element(By.CSS_SELECTOR, "h2")
        print(f"Result element text: {result_element.text}")

        # Check if the result indicates an error or failure
        if result_element.text == "STDERR:" or "failed" in result_element.get_attribute("class"):
            print("Challenge Failed or STDERR found, attempting to debug.")
            # Extract the failed outputs
            failed_outputs_elements = driver.find_elements(By.CSS_SELECTOR, ".result-type__value.failed")
            failed_outputs = [element.text for element in failed_outputs_elements]
            print(f"Failed outputs: {failed_outputs}")

            # Attempt to extract STDERR details if present
            stderr_text = None
            try:
                stderr_text_element = driver.find_element(By.CSS_SELECTOR, ".result-type--error pre")
                stderr_text = stderr_text_element.text
                print(f"STDERR text: {stderr_text}")
            except:
                print("No STDERR text found.")

            # Call aiDebugger to debug the code
            debugged_code = aiDebugger(api_key, description_text, cleaned_response, failed_outputs, stderr_text)

            if debugged_code:
                debugged_cleaned = cleanResponse(debugged_code)
                print("Debugged code received and cleaned.")
                # Switch back to the main content and clear the CodeMirror editor
                driver.switch_to.default_content()
                driver.execute_script("arguments[0].CodeMirror.setValue('');", code_mirror)
                # Paste the debugged and cleaned code
                driver.execute_script("arguments[0].CodeMirror.setValue(arguments[1]);", code_mirror, debugged_cleaned)
                print("Debugged code pasted into the editor.")
                # Click the attempt button again to test the debugged code
                driver.execute_script("arguments[0].click();", attempt_button)
                print("Attempt button clicked again.")
                time.sleep(10)

                # Switch back to the iframe containing the test results
                iframe = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "runner_frame"))
                )
                driver.switch_to.frame(iframe)
                print("Switched back to runner iframe.")
                # Wait for the result summary to be present and retrieve it
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h2"))
                )
                result_element = driver.find_element(By.CSS_SELECTOR, "h2")
                print(f"Result element text after debugging: {result_element.text}")

                if result_element.text == "STDERR:" or "failed" in result_element.get_attribute("class"):
                    # If the challenge failed again, skip it
                    print("Challenge Failed again or STDERR found, skipping challenge.")
                    driver.switch_to.default_content()
                    skip_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "skip_btn"))
                    )
                    driver.execute_script("arguments[0].click();", skip_button)
                    time.sleep(2)
                else:
                    # If the challenge passed, submit it
                    print("Challenge Passed after debugging.")
                    driver.switch_to.default_content()
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "submit_btn"))
                    )
                    driver.execute_script("arguments[0].click();", submit_button)

                    # Vote for the challenge to gain honor points
                    vote_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "icon-moon-happy"))
                    )
                    driver.execute_script("arguments[0].click();", vote_button)
                    print("Voted for +1 Honor!")
                    time.sleep(2)

                    # Proceed to the next kata
                    next_kata_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "play_next_btn"))
                    )
                    driver.execute_script("arguments[0].click();", next_kata_button)
                    problem_counter[0] += 1
                    print(f"Problems solved: {problem_counter[0]}")
                    time.sleep(3)
                    wait_for_train_button(driver)
            else:
                # If debugging failed, skip the challenge
                print("Failed to debug the challenge.")
                driver.switch_to.default_content()
                skip_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "skip_btn"))
                )
                driver.execute_script("arguments[0].click();", skip_button)
                time.sleep(2)
        else:
            # If the challenge passed on the first attempt, submit it
            print("Challenge Passed.")
            driver.switch_to.default_content()
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "submit_btn"))
            )
            driver.execute_script("arguments[0].click();", submit_button)

            # Vote for the challenge to gain honor points
            vote_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "icon-moon-happy"))
            )
            driver.execute_script("arguments[0].click();", vote_button)
            print("Voted for +1 Honor!")
            time.sleep(2)

            # Proceed to the next kata
            next_kata_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "play_next_btn"))
            )
            driver.execute_script("arguments[0].click();", next_kata_button)
            problem_counter[0] += 1
            print(f"Problems solved: {problem_counter[0]}")
            time.sleep(5)
            wait_for_train_button(driver)
    except Exception as e:
        print(f"An error occurred while solving a challenge: {e}")

def wait_for_train_button(driver):
    # Waits for the train button to become clickable and clicks it
    try:
        while True:
            try:
                # Wait for the train button and click it when available
                train_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "play_btn"))
                )
                driver.execute_script("arguments[0].click();", train_button)
                print("Train button found, ready to proceed.")
                break
            except:
                # If the train button is not found, click the next kata button
                next_kata_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "play_next_btn"))
                )
                driver.execute_script("arguments[0].click();", next_kata_button)
                print("Next Kata button clicked.")
                time.sleep(3)
    except Exception as e:
        print(f"An error occurred while waiting for the train button: {e}")

def train(api_key, username, password, chromedriver_path):
    # Initiates the driver, logs in, and starts the challenge-solving process
    service = webdriver.chrome.service.Service(chromedriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)

    # Counter to track the number of problems solved
    problem_counter = [0]
    login(driver, username, password)

    # Continuously solve challenges
    while True:
        solve_challenge(driver, api_key, problem_counter)

    driver.quit()

if __name__ == "__main__":
    # Read configurations from the configuration file
    configs = read_configs('configs.txt')
    api_key = configs['API_KEY']
    email = configs['EMAIL']
    password = configs['PASSWORD']
    chromedriver_path = configs['CHROMEDRIVER_PATH']

    # Start training process
    train(api_key, email, password, chromedriver_path)
