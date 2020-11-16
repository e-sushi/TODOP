# TODOP
A python script that parses your code and indexes your TODOs for you.

There are two versions of TODOP in this repo, TODOP_GIT and TODOP.

TODOP takes in a local directory and scans through the entire thing to find TODOs of a certain format then places them in a TODOs.txt file. 
TODOP_GIT does a lot more and is explained more below.

The format for both scripts is
`TODO(tags, author, date, title) body`

TODOP_GIT is set up to run as a server that listens for webhooks from a github repository and then runs the same script as TODOP, but with some functionality that allows it to automatically add issues to a repo
It uses Flask to run the server and if you want to use it, you'll have to set up your own domain to send webhooks to. I use NO-IP.

This is not configured as a Github App (yet, probably), so I run it through another account that has access to my repos.
