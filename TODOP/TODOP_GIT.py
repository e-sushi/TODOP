
import os
import sys
import fileinput
from github import Github
import github
from flask import Flask, request, Response
import json
import base64
import time

#events are received 5 minutes after they occur

#this version of TODOP is meant to be ran as a server that listens
#for push webhooks from a repository

#important stuff here
#ENTER_GITHUB_PERSONAL_ACCESS_TOKEN_HERE
GITTOKEN = "ENTER_GITHUB_PERSONAL_ACCESS_TOKEN_HERE"
REPO = "SushiSalad/P3DPGE"
APP_ID = 88527

app = Flask(__name__)



@app.route('/webhook', methods=['POST'])
def respond():
	payload = request.get_json()
	print(payload)
	main()
	return Response(status=200)

@app.route('/', methods=['GET'])
def hello_world():
	return "TODOP time"

def find_files_git(repo, exts):
	contents = repo.get_contents("")
	files = []
	while contents:
		file = contents.pop(0)
		if file.type == "dir":
			contents.extend(repo.get_contents(file.path))
		else:
			for ext in exts:
				if file.name.endswith(ext):
					files.append(file)
	return files;

def find_files(dir_name, exts):
	filepaths = []
	
	for root, dirs, files in os.walk(dir_name):
		for file in files:
			for ext in exts:
				if file.endswith(ext):
					filepaths.append(os.path.join(root, file))
	return filepaths

def getTODOs(file):
	TODOs = []
	line_num = 0
	for line in file:
		if "TODO(" in line:
			TODO = line[line.find("TODO("):]
			arguments = TODO[TODO.find("(") + 1:TODO.find(")")].split(",")
			body = TODO[TODO.find(")") + 1:]
			TODOs.append((file.name, line_num, arguments, body))
		line_num += 1
	return TODOs
	
def getTags(tagsList):
	Tags = []
	for tag in tagsList:
		if "+" in tag:
			Tags.append("GitIssue")
		if "s" in tag and "u" in tag:
			Tags.append("CHECK_TAGS")
		else:
			if "s" in tag:
				Tags.append("Severe")
			if "u" in tag:
				Tags.append("Unimportant")
		if "p" in tag:
			Tags.append("Physics")
		if "r" in tag:
			Tags.append("Render")
		if "e" in tag:
			Tags.append("Entity")
		if "i" in tag:
			Tags.append("Input")
		if "m" in tag:
			Tags.append("Math")
		if "o" in tag:
			Tags.append("Optimization")
		if "g" in tag:
			Tags.append("General")
		if "c" in tag:
			Tags.append("Clean-Code")
	if len(Tags) == 0:
		Tags.append("No Tags")
	return Tags

def main():
	g = Github(GITTOKEN)
	repo = g.get_repo(REPO)
	
	code = open("code.txt", "w")
	if not os.path.exists("code"):
		os.makedirs("code")

	#turn decoded files into usable shit
	wrote_new = False
	wrote_tab = False
	filePaths = find_files_git(repo, ['.cpp', '.h'])
	for file in filePaths:
		temp_code = open("code\\" + file.name, "w")
		for b, a in zip(str(file.decoded_content), str(file.decoded_content)[1:]):
			if not wrote_tab or not wrote_new:
				if wrote_tab:
					wrote_tab = False
				elif wrote_new:
					wrote_new = False
				else:
					if b == "\\" and a == "n":
						temp_code.write("\n")
						wrote_new = True
					elif b == "\\" and a == "t":
						temp_code.write("\t")
						wrote_tab = True
					else:
						temp_code.write(b)
						wrote_new = False
						wrote_tab = False

	print("\n-Collecting TODOs")
	TODOs = []
	filePaths = find_files("code\\", ['.cpp', '.h'])
	for filePath in filePaths:
		file = open(filePath, 'r')
		fileTODOS = getTODOs(file)
		TODOs.extend(fileTODOS)
		print("  %d TODOs from %s" % (len(fileTODOS), filePath.split("\\")[-1]))
		file.flush()
		file.close()
	print("-Collected %d TODOs from %d files" % (len(TODOs), len(filePaths)))

	#make room for listing number of TODOs later
	TODOList = open("TODOs_GIT.txt", "w+")
	TODOList.write("TODO List successfully generated with " + str(len(TODOs)) + " TODOs found.\n\n")
	TODO_num = 0
	for file_name, line_num, arguments, body in TODOs:
		Tags = getTags(arguments[0])

		#writes all the TODOs to the file with formatting
		TODOList.write("~~~~~~~ TODO " + str(TODO_num) + " ~~~~~~~\n")
		if len(arguments) == 4: TODOList.write("Title: " + arguments[3] + "\n")
		TODOList.write(file_name[file_name.rfind("\\") + 1:] + ", Line: " + str(line_num) + "\n")
		TODOList.write("Creator: " + arguments[1] + "\n")
		if len(arguments) == 5: TODOList.write("Assigned to:" + arguments[4] + "\n")
		TODOList.write("----------------------\n")
		if len(arguments) == 3: TODOList.write("Date: " + arguments[2] + "\n")
		TODOList.write("Tags: ")
		for i, tag in enumerate(Tags):
			TODOList.write(tag)
			if i != len(Tags) - 1: TODOList.write(", ")
		TODOList.write("\n----------------------\n")
		if body[0] == " ":
			TODOList.write(body[1:])
		else:
			TODOList.write(body)
		#TODOList.write("~~~~~~~ TODO " + str(TODO_num) + " ~~~~~~~")
		#TODOList.write("\n\n\n")
		TODOList.write("\n")
		TODO_num += 1
		
		#updates all the TODO issues
		

	#updates the repo's TODO.txt file
	TODOList.seek(0)
	repo_files = []
	contents = repo.get_contents("")
	while contents:
		file = contents.pop(0)
		if file.type == "dir":
			contents.extend(repo.get_contents(file.path))
		else:
			repo_files.append(file.name)

	if "TODOs.txt" in repo_files:
		contents = repo.get_contents("TODOs.txt")
		repo.update_file(contents.path, "Update TODOs", TODOList.read(), contents.sha)
	#else:
		repo.create_file("TODOs.txt", "Create TODOs.txt", TODOList.read())
	print("-Finished updating TODOs on Github")
	TODOList.close()
	
	

if __name__ == "__main__":
	main()
	#app.run(host="0.0.0.0", port = 80, threaded = True, debug = False)
	
	
