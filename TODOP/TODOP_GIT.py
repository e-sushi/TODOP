import os
import sys
import fileinput
from github import Github
import github
from flask import Flask, request, Response
import json

#this version of TODOP is meant to be ran as a server that listens
#for push webhooks from a repository
#this is very hacked together sorry lol

#important stuff here
GITTOKEN = "YOUR_GIT_TOKEN_HERE"
REPO = "YOUR_REPO_HERE"

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def respond():
	payload = request.get_json()
	p = payload['pusher']['name']
	if "TODOPBOT" not in p:
		main()

	return Response(status=200)

@app.route('/index.html', methods=['GET'])
def hello_world():
	return "TODOP TIME!"

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
	Tags.append("TODOP")
	for tag in tagsList:
		if "+" in tag:
			Tags.append("GitIssue")
		if "s" in tag and "u" in tag:
			Tags.append("CHECK_TAGS")
		else:
			if "s" in tag:
				Tags.append("severe")
			if "u" in tag:
				Tags.append("unimportant")
		if "p" in tag:
			Tags.append("physics")
		if "r" in tag:
			Tags.append("render")
		if "e" in tag:
			Tags.append("entity")
		if "i" in tag:
			Tags.append("input")
		if "m" in tag:
			Tags.append("math")
		if "o" in tag:
			Tags.append("optimization")
		if "g" in tag:
			Tags.append("general")
		if "c" in tag:
			Tags.append("clean up")
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
		#write title if there is one
		if len(arguments) >= 4: TODOList.write("Title: " + arguments[3] + "\n")
		#write the file the TODO was found in and what line
		TODOList.write(file_name[file_name.rfind("\\") + 1:] + ", Line: " + str(line_num) + "\n")
		#write the creator's name
		TODOList.write("Creator: " + arguments[1] + "\n")
		TODOList.write("----------------------\n")
		#write the date signed on the TODO
		if len(arguments) >= 3: TODOList.write("Date: " + arguments[2] + "\n")
		#write tags
		TODOList.write("Tags: ")
		for i, tag in enumerate(Tags):
			TODOList.write(tag)
			if i != len(Tags) - 1: TODOList.write(", ")
		TODOList.write("\n----------------------\n")
		if body[0] == " ":
			TODOList.write(body[1:])
		else:
			TODOList.write(body)
		TODOList.write("\n")
		TODO_num += 1
		
		#updates all the TODO issues
		
		#create a new issue in the repo if an issue has the "+" tag
		make_issue = True
		if "GitIssue" in Tags and "CHECK_TAGS" not in Tags:
			#tags to labels
			_labels = []
			repolabels = repo.get_labels()
			for label in repolabels:
				if label.name in Tags:
					_labels.append(label)
			print(_labels)

			open_issues = repo.get_issues(state = 'open')
			for issue in open_issues:
				if len(arguments) == 4:
					if issue.title == arguments[3]:
						make_issue = False
				elif issue.title == body[:20]:
					make_issue = False

			if make_issue:
				il = open("open_issues.txt", "a")
				if len(arguments) >= 3: TSign = "\nTODO created by " + arguments[1] + " on " + arguments[2] + "\nThis issue is located in file " + file_name[file_name.rfind("\\") + 1:] + " on line " + str(line_num) + "\n\nGenerated automatically by TODOP.py"
				else: TSign = "\nTODO created by " + arguments[1] + "\nGenerated automatically by TODOP.py"
				#create with title and assignee
				if len(arguments) == 5: 
					issue = repo.create_issue(arguments[3], body + TSign, labels = _labels)
				
				#create with title
				elif len(arguments) == 4: 
					issue = repo.create_issue(arguments[3], body + TSign, labels = _labels)

				#create with part of body as title
				elif len(arguments) <= 3: 
					issue = repo.create_issue(body[:20] + "...", body + TSign, labels = _labels)

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
		sha = repo.get_branch(branch="master").commit.sha
		commit = repo.get_commit(sha=sha)
		repo.update_file("TODOs.txt", commit.author.login + ": " + commit.commit.message, TODOList.read(), contents.sha)
	else:
		repo.create_file("TODOs.txt", "Create TODOs.txt", TODOList.read())
	print("-Finished updating TODOs on Github")

	#close issues if they no longer exist in the files
	TODOP_LABEL = []
	TODOP_LABEL.append(repo.get_label("TODOP"))
	issues = repo.get_issues(labels = TODOP_LABEL)
	title = ""
	print(issues)
	for issue in issues:
		print("Looking for: " + issue.title)
		TODOList.seek(0)
		delete = True
		if issue.title.endswith("..."):
			title = issue.title[:issue.title.find("...")]
		else:
			title = issue.title
		for line in TODOList:
			if title[1:] in line:
				delete = False
		if delete:
			print("\nClosing " + issue.title + "because it was not found in the latest TODO scan.")
			issue.edit(state="close")
	
	

if __name__ == "__main__":
	app.run(host="0.0.0.0", port = 80, threaded = True, debug = False)
	
	
