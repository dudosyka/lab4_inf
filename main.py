from json2xml import json2xml
from json2xml.utils import readfromstring
import re
import time
import matplotlib.pyplot as plt

page = open('./table.html').read()

rows = page.split("<tr>")


def createJsonField(name, value, needComma=True):
    if type(value) == str:
        item = "\n\t\"" + name + "\": \"" + value + "\"" + ("," if needComma else "")
    else:
        item = "\n\t\"" + name + "\": [" + ", ".join(value) + "]" + ("," if needComma else "")
    return item


def parseInputFile(page):
    json = "{\n"
    day = ""
    subjects = []
    for i in range(1, len(rows) - 1):
        row = rows[i]
        items = row.split('<td')
        time = ""
        weeks = []
        auditory = ""
        corp = ""
        subject = ""
        teacher = ""
        format = ""
        for item in items:
            name = item.split("\"")[1]
            if day == "" and name == 'day':
                day = item.split("<span>")[1].split("</span>")[0]
            if name == "time":
                time = item.split("<span>")[1].split("</span>")[0]
                weeks = list(map(str, item.split("<div>")[1].split("</div>")[0].split(", ")))
            if name == "room":
                auditory = item.split("<dd>")[1].split("</dd>")[0]
                corp = item.split("<span>")[1].split("</span>")[0]
            if name == 'lesson':
                subject = item.split("<dd>")[1].split("</dd>")[0]
                teacher = item.split("<b>")[1].split("</b>")[0]
            if name == 'lesson-format':
                format = item.split(">")[1].split("<")[0]
        subjects.append("\n{\n" \
                        + (createJsonField("time", time)
                           + createJsonField("weeks", weeks)
                           + createJsonField("auditory", auditory)
                           + createJsonField("corp", corp)
                           + createJsonField("name", subject)
                           + createJsonField("teacher", teacher)
                           + createJsonField("format", format, False)) \
                        + "\n}")

    json += createJsonField("weekday", subjects, False) + "\n}"
    return json


def createXMLTag(name, value, addBlankLine=False, autoType=True, setType=""):
    fieldType = ""
    if autoType:
        fieldType = "type=\"str\"" if type(value) == str else "type=\"list\""
        fieldType = "type=\"int\"" if type(value) == int else fieldType
    else:
        fieldType = "type=\"" + setType + "\""
    if type(value) == str or type(value) == int:
        return ("\n" if addBlankLine else "") + "<" + name + " " + fieldType + ">" + str(value).strip(" ") + (
            "\n" if addBlankLine else "") + "</" + name + ">"
    else:
        return "<" + name + ">\n\t\t" + "\n\t\t".join(
            list(map(lambda el: createXMLTag("item", int(el)), value))) + "\n\t</" + name + ">"


def parseToXMLVanilla(json):
    rows = json.split("{")
    xml = ""
    for i in range(2, len(rows)):
        row = rows[i]
        item = row.split("\n")
        lesson = ""
        for j in range(2, len(item) - 2):
            key = item[j].split("\": ")[0].split("\"")[1]
            value = item[j].split("\": ")[1].strip(",").strip("\"")
            if value.rfind("[") != -1:
                value = list(map(str, value.strip("[").strip("]").split(",")))
            lesson += "\n\t" + createXMLTag(key, value)
        xml += createXMLTag("lesson", lesson, True, False, "dict")
    xml += "\n"
    output = open("./output_vanilla.xml", "w")
    output.write("")
    output.write("<?xml version=\"1.0\" ?>\n" + createXMLTag("timetable", xml, False, False, "list"))


def parseToXMLLib(json):
    output = open("./output_lib.xml", "w")
    output.write(json2xml.Json2xml(readfromstring(json)).to_xml())


def parseToXMLRegex(json):
    res = re.findall(r"\"(\w+)\"\:\s*(\"|\[)(.*){1}(\,|\n)", json)
    parent = res[0]
    first = ""
    xml = ""
    lesson = ""
    for i in range(1, len(res)):
        item = res[i]
        if (item[1] == "\""):
            value = item[2].strip(",").strip("\"")
        else:
            value = list(map(str, item[2].strip(",").strip("]").split(", ")))

        if (first == item[0]):
            xml += createXMLTag("lesson", lesson, True)
            lesson = ""

        lesson += "\n\t" + createXMLTag(item[0], value)
        if (first == ""):
            first = item[0]

    if lesson != "":
        xml += createXMLTag("lesson", lesson, True, False, "dict") + "\n"
    output = open("./output_regex.xml", "w")
    output.write("")
    output.write("<?xml version=\"1.0\" ?>\n" + createXMLTag("timetable", xml))


def parseToCsv(json):
    res = re.findall(r"\"(\w+)\"\:\s*(\"|\[)(.*){1}(\,|\n)", json)
    parent = res[0]
    first = ""
    csv = "sep=$\n"
    row = ""
    for i in range(1, len(res)):
        item = res[i]
        value = item[0]

        if (first == item[0]):
            csv += row.strip("$") + "\n"
            row = ""
            break
        if (first == ""):
            first = item[0]
        row += value + "$"
    first = ""
    for i in range(1, len(res)):
        item = res[i]
        if (item[1] == "\""):
            value = item[2].strip(",").strip("\"")
        else:
            value = item[2].strip(",").strip("]")

        if (first == item[0]):
            csv += row.strip("$") + "\n"
            row = ""

        row += value + "$"
        if (first == ""):
            first = item[0]

    if row != "":
        csv += row.strip("$")
    output = open("./output.csv", "w")
    output.write("")
    output.write(csv)


def checkEfficiency(func, json):
    efficiency = list()
    for i in range(500):
        startTime = round(time.time() * 1000)
        func(json)
        endTime = round(time.time() * 1000)
        efficiency.append(endTime - startTime)
    return efficiency


json = parseInputFile(page)

input = open("./input.json", "w")
input.write(json)

# parseToXMLVanilla(json)
# parseToXMLLib(json)
# parseToXMLRegex(json)
# parseToCsv(json)
vanillaEfficiency = checkEfficiency(parseToXMLVanilla, json)
libEfficiency = checkEfficiency(parseToXMLLib, json)
regexEfficiency = checkEfficiency(parseToXMLRegex, json)

# x-coordinates of left sides of bars
left = [1, 2, 3]

# heights of bars
height = [sum(vanillaEfficiency), sum(libEfficiency), sum(regexEfficiency)]

# labels for bars
tick_label = ['Vanilla', 'Lib', 'Regex']

# plotting a bar chart
plt.bar(left, height, tick_label=tick_label,
        width=0.8, color=['red', 'green'])

# naming the x-axis
plt.xlabel('Parser type')
# naming the y-axis
plt.ylabel('Summary time in 10 iterations (ms)')
# plot title
plt.title('Parser efficiency')

# function to show the plot
plt.show()