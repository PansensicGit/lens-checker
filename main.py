import os
import re
from ruamel.yaml import YAML
import io
import regex as re

def walkLevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]

def retrieveItems(path,ignoreItems=[
    'node_modules',
    'dist',
    'build',
    'coverage',
    'docs',
    'public',
    'src',
    'test',
    'tests',
    'vendor',
    'bin',
    'tmp',
    '.git',
    '.github',
    'lenses-checker'
]):
    item = []

    for root, dirs, files in walkLevel(path,0):
        for dir in dirs:
            item.append(dir)

    for folder in ignoreItems:
        if folder in item:
            item.remove(folder)
            
    return item

def checkLensName(lens):
    if not re.match(r'^\d+\s', lens):
        raise Exception("Lens does not start with a number: '{}'".format(lens))

def checkForDuplicates(item):
    seen = set()
    duplicates = set(x for x in item if x in seen or seen.add(x))
    if len(duplicates) > 0:
        raise Exception("Duplicate item found: '{}'".format(duplicates))
    return item

def checkIfString(value):
    if not isinstance(value, str):
        raise Exception("value is not a string: '{}'".format(value))

def checkFileExists(path):
    return os.path.isfile(path)

def loadYamlFile(path):
    yaml=YAML(typ='safe')
    with io.open(path, 'r', encoding='utf8') as stream:
        return yaml.load(stream)

def checkIfFloat(value):
    if not isinstance(value, float):
        raise Exception("value is not a float: '{}'".format(value))

def checkIfFloatOrInteger(value):
    if not isinstance(value, float) and not isinstance(value, int):
        raise Exception("value is not a float or integer: '{}'".format(value))

def checkIfInteger(value):
    if not isinstance(value, int):
        raise Exception("value is not an integer: '{}'".format(value))

def checkIfText(value):
    if not isinstance(value, str):
        raise Exception("value is not text: '{}'".format(value))

def retrieveYamlFiles(path):
    yamlFiles = []
    for root, dirs, files in walkLevel(path,1):
        for file in files:
            if file.endswith('.yaml'):
                yamlFiles.append(os.path.join(root, file))
    return yamlFiles

def compileRegex(regexPattern):
    try:
        re.compile(regexPattern)
    except re.error:
        raise Exception("Invalid regex: '{}'".format(regexPattern))

def convertPhraseSyntaxToText(phrase):
    # 1. Asterisk: * represents a wild card for any alphanumeric characters - I suggest substituting simply "abc".
    # 2. Alphabetic characters: [a] represents any single letter, [aa] represents any 2 letters, [aaa] represents any 3 letters - if you simply strip out the square brackets that will work fine in this case.
    # 3. Numeric characters: similar to above, [n] represents any digit, [nn] represents any 2 digits, etc - here the "n"s need replacing with digits, say "1"s, then the square brackets dropped.

    #anxi* about the change[a]
    #amalgamat*
    #chang* * needed
    #cop* with change
    #de[a]merger

    phrase = phrase.replace('*', 'abc')

    #replace any number of a's in a squared bracket with the same number of a's
    phrase = re.sub(r'\[a+\]', lambda m: 'a' * (len(m.group(0))-2), phrase)

    #replace any nubmer of n's in a squared bracket with the same number of 1's
    phrase = re.sub(r'\[n+\]', lambda m: '1' * (len(m.group(0))-2), phrase)

    phrase = phrase.replace('-', 'H') \
        .replace("'", 'A') \
        .replace("`", 'A') \
        .replace('&', 'X') \
        .replace('. ', ' F ') \
        .replace('!', ' E ') \
        .replace('?', ' Q ')

    return phrase

def isMatchFound(regexPattern, phrase):
    if re.search(regexPattern, phrase):
        return True
    return False

if __name__ == "__main__":
    cwd = os.getcwd()

    lenses = retrieveItems(cwd)
    print(lenses)
    
    checkForDuplicates(lenses)

    if len(lenses) == 0:
        raise Exception("No lenses found")
    
    for lens in lenses:
        checkLensName(lens)

        lensYaml = os.path.join(cwd,lens,'lens.yaml')
        if checkFileExists(lensYaml):
            lensYamlContents = loadYamlFile(lensYaml)
            if lensYamlContents:
                lensID = lensYamlContents.get('lensID')
                lensName = lensYamlContents.get('name')
                checkIfInteger(lensID)
                checkIfText(lensName)
            else:
                raise Exception("lens.yaml is incorrect for '{}'".format(lens))
        else:
            raise Exception("Lens '{}' is missing lens.yaml".format(lens))

        buckets = retrieveYamlFiles(lens)
        if len(buckets) == 0:
            raise Exception("Lens '{}' is missing buckets ".format(lens))

        for bucket in buckets:
            if bucket.endswith('lens.yaml'):
                buckets.remove(bucket)

        checkForDuplicates(buckets)
        for bucket in buckets:
            bucketsYamlContents = loadYamlFile(bucket)
            if bucketsYamlContents:
                regexs = bucketsYamlContents.get('regexs')
                bucketStats = bucketsYamlContents.get('bucketStats')
                bucketInfo = bucketsYamlContents.get('bucketInfo')

                # print(bucket)
                # print(bucketStats)

                if bucketStats:
                    defaultRegexWeight = bucketStats.get('defaultRegexWeight')
                    multiplier = bucketStats.get('multiplier')
                    checkIfInteger(defaultRegexWeight)
                    checkIfInteger(multiplier)
                else:
                    raise Exception("bucketStats is missing for '{}'".format(bucket))

                if bucketInfo:
                    bucketName = bucketInfo.get('name')
                    bucketID = bucketInfo.get('bucketID')
                    lensID = bucketInfo.get('lensID')
                    checkIfText(bucketName)
                    checkIfInteger(bucketID)
                    checkIfInteger(lensID)
                else:
                    raise Exception("bucketInfo is missing for '{}'".format(bucket))

                if regexs:
                    for regexItem in regexs:
                        regexPattern = regexItem.get('regex')
                        phrase = regexItem.get('phrase')
                        weight = regexItem.get('weight')

                        if phrase:
                            checkIfString(phrase)

                        if regexPattern:
                            checkIfString(regexPattern)

                        if weight:
                            checkIfFloatOrInteger(weight)

                        sampleComment = convertPhraseSyntaxToText(phrase)

                        #dont include any spaces or words after the phrase if the last character is a number, as its valid in k2o
                        if phrase[-1].isdigit():
                            matches = isMatchFound(regexPattern,sampleComment)
                        else:
                            sampleCommentWithSpaceAndBlankWord = sampleComment + " blankword"
                            matches = isMatchFound(regexPattern,sampleCommentWithSpaceAndBlankWord)

                        #If the regex matches the sample comment, then the regex for matches
                        if not matches:
                                raise Exception("Regex does not match phrase. Lens: '{}' Bucket: '{}' Regex: '{}' Phrase: '{}' Sample Comment: '{}' Matches: '{}'".format(lens, bucketName, regexPattern, phrase, sampleCommentWithSpaceAndBlankWord, matches))

            else:
                raise Exception("bucket yaml is incorrect for '{}'".format(bucket))