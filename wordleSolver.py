import os
import io
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time 

CORRECT = '!!!!!'
# PATH = "IAPT\chromedriver.exe"

driver = webdriver.Chrome(ChromeDriverManager().install())

def getWords():
  valids = []
  allWords = []
  tmpWord = ""
  fnlWord = ""
  # f = io.open("malta-wordle.txt", mode="r", encoding="utf-8")
  f = io.open("dictionary.txt", mode="r", encoding="utf-8")
  for line in f:
    #get first word in line (contains word)
    currWord = line.split(None, 1)[0].lower()
    
    # if no "għ" or "ie" are found, this is appended
    allWords.append(currWord)

  for currWord in allWords:
    #remove tags and artikli (invalid words)
    if len(currWord) == 5 and currWord[-1] != '-' and currWord[0] != '<':
      valids.append(currWord)

  FIVEL_WORDS = valids
    
  return FIVEL_WORDS


def accept(driver):
    driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm.swal2-styled").click()
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm.swal2-styled").click()
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, "button.swal2-deny.swal2-styled").click()
    time.sleep(0.5)

#main class
def solve():
  # open website and accept terms
  driver.get("https://wordle-malti.github.io/")

  accept(driver)

  #for time statistic
  start_time = time.time()

  checkedWords = {}
  valid_words = getWords()
  valid_words = list(dict.fromkeys(valid_words))
  # for i in range(len(valid_words)):
  #   valid_words[i] = valid_words[i].lower()
  guessCnt = 0
  while True:
    guessCnt += 1
    guess = make_guess(valid_words, checkedWords)

    output_guess(driver, guess)
    
    result = collect_result(driver, guessCnt)
    if result == CORRECT:
        print("I won!")

        print("Time taken: " + "--- %s seconds ---" % (time.time() - start_time))
        break

    valid_words = update_valid_words(valid_words, guess, result, 0, checkedWords)
    
    for item in valid_words:
      txt2 = item.encode('utf-8')
      fp = open("guesses.txt", "ab")
      fp.write(txt2)
      fp = open("guesses.txt", "a")
      fp.write("\n")

    print()


import random
from collections import Counter

def make_guess(valid_words, checkedWords):
  if len(valid_words) < 500:
    return make_guess_exhaustive(valid_words, checkedWords)
  else:
    return make_guess_freq(valid_words)

def output_guess(driver, guess):
      outputGuess = ""
      outputGuess = guess
      outputGuess = guess.replace("?", "ie")
      outputGuess = guess.replace("/", "għ")

      driver.find_element(By.CSS_SELECTOR, "td.guess_box.ng-binding.ng-scope").click()
      actions = ActionChains(driver)
      # actions.send_keys("papra")
      actions.send_keys(outputGuess)
      actions.send_keys(Keys.ENTER)
      # actions.send_keys(outputGuess)
      actions.perform()


def make_guess_exhaustive(valid_words, checkedWords):
  all_words = getWords()
  #guessable_words = all_words if len(valid_words) <50 else valid_words
  #guessable_words = valid_words if len(valid_words) == 1 or len(valid_words) == 2 or len(valid_words) > 50 else all_words #if len(valid_words) <50 else valid_words

  if len(valid_words) == 1 or len(valid_words) == 2  or len(valid_words) > 50:
    guessable_words = valid_words
  
  # If there are multiple words with everything the same except one letter (MATCH, CATCH, BATCH, HATCH, WATCH )
  else:
    guessable_words = all_words

  
  guess = None
  lowest_worst_score = len(valid_words) + 1
  lowest_total_score = len(valid_words) ** 2
  # for possible_guess in valid_words: THIS MIGHT BE RIGHT
  for possible_guess in guessable_words:
    # First, figure out the worst possible and total/average remaining words for this guess
    worst_score = 0
    total_score = 0
    for possible_answer in valid_words:
      #get what the result be for current word
      result = get_result(possible_guess, possible_answer)    
      num_new_valid_words = len(update_valid_words(valid_words, possible_guess, result, 1, checkedWords))
      worst_score = max(num_new_valid_words, worst_score)
      total_score += num_new_valid_words
      
    # If this possble guess has a lower total/average number of words remaining, use it instead
    if worst_score < lowest_worst_score:
      guess = possible_guess
      lowest_worst_score = worst_score
      lowest_total_score = total_score
    # If it's a tie in average words remaining, choose the one that doesn't have the worst case
    elif worst_score == lowest_worst_score and total_score < lowest_total_score:
      guess = possible_guess
      lowest_worst_score = worst_score
      lowest_total_score = total_score
  return guess

def make_guess_freq(valid_words):
  # Figure out the counts first     
  counts = Counter()
  for word in valid_words:
    counts.update(word)
  # Now score the words based on their counts     
  # This will be a list of tuples (score, word)     
  word_scores = []
  for word in valid_words:
    unique_chars = set(word)
    word_score = sum([counts.get(c) for c in unique_chars])
    word_scores.append((word_score, word))
  # Sort the list and pick the highest score  (word with most freq. letters)   
  return sorted(word_scores, reverse=True)[0][1]
  
import re
def collect_result(driver, guessCnt):
  result = ""
  # ele = driver.find_element(By.XPATH, "//table/tbody/tr[1]/td[5]")
  for letterCnt in range(1,6):
    ele = driver.find_element(By.XPATH, "//table/tbody/tr[{guess}]/td[{letter}]".format(guess = guessCnt, letter = letterCnt))
    letterResult = ele.get_attribute("class")

    if(letterResult == "orange"):
      result += "?"
    elif(letterResult == "green"):
      result += "!"
    else:
      result += "_"
    
  # Collect the result of our guess from the user
  match = re.match(r'^[!?_]{5}$', result)

  if not match:
    print("Invalid response string, try again")
    return collect_result()
  return result

def get_result(guess, answer):
  # Given a guess and a known answer, return the result
  result = ""
  for pos, ch_guess, ch_answer in zip(range(5), guess, answer):
    if ch_guess == ch_answer:
      result += "!"
    elif ch_guess not in answer:
      result += "_"
    else:
      result += "?"
  return result
  
def update_valid_words(valid_words, guess, result, hardFilter, checkedWords):
  if(hardFilter == 0):
    for cnt, letter in enumerate(guess):

      if result[cnt] == '!':
        valid_words = [x for x in valid_words if letter in x]

      elif result[cnt] == '_':
        # if not already seen in dictionary as green or orange
        if letter in checkedWords.keys():
          if(checkedWords[letter] != "?" and checkedWords[letter] != "!"):
            valid_words = [x for x in valid_words if letter not in x]
        
        #if it has not been seen in dictionary
        else:
          #check if its a duplicate( since they act different) - if this is grey there might be a green/orange later in word
            isDup = False
            secondCnt = 0
            nextL = cnt+1
            for otherL in guess[nextL::]:
              secondCnt += 1
              if otherL == letter:
                isDup == True
                check = cnt+secondCnt
                if result[check] == "_":
                  valid_words = [x for x in valid_words if letter not in x]

            if isDup == False:
              valid_words = [x for x in valid_words if letter not in x]

      elif result[cnt] == "?":
        if letter not in checkedWords.keys():
          checkedWords[letter] = "?"
        valid_words = [x for x in valid_words if letter in x]
        tmp_validW = valid_words
        for word in tmp_validW:
          if word[cnt] == letter:
            valid_words.remove(word)

    
  # return valid_words
  maybeReturn = [word for word in valid_words if get_result(guess, word) == result]
  if(len(maybeReturn) == 0):
    return valid_words
  else:
    return maybeReturn
    #return [word for word in valid_words if get_result(guess, word) == result]  #compare current word with every valid word (if they get the same result, it means they are eligible)

solve()