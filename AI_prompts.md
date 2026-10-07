# AI Prompts Log — HW 4

One section per problem. Each section has the problem number and title, the prompts typed in, and follow-up prompts when more than one was needed.

The running site, database writes, and screenshots are the homework evidence. This file is the log of prompts typed to the coding assistant.

Assignment: 13 problems. Build a real Campus Customs / Yale Bulldog Blue customer website with a helpful chatbot. Class setting only (not a partnership with the shop). Front end is React + Vite + TypeScript. Back end is Python FastAPI. The chatbot brain is a PydanticAI agent. Shoppers browse products, create an account, and chat about merch. Matching items appear on the page. Price and stock answers come from a local SQLite database and must be honest. Use `PORTKEY_API_KEY` and **gpt-5.6-lunar**. Say so before switching to a stronger model. Work one problem at a time. At the end, push the project to a public GitHub repo and submit the repo URL.

Data, once copied into this folder:

- `data/campus_customs.db` — SQLite with `catalogue`, `inventory`, and `users` (hashed passwords). The download also has a `chat_messages` table.
- `data/products/` — product images. Paths match `catalogue.image_file_path`.

---

## Problem 1: Vibe code prompts

**Prompt I typed in**

```
ready for hw 4?
```

**Follow-up prompts**

```
so first lets begin with the scenario to get you the concept of what we're doing
```

```
the scenario is that campus customs needs a real customer website with a helpful chatbot. we 're gonna build a react + vite typescript front end and a python fastapi backend whose brain is a pydanticAi agent. Shoppers should be able to browse products, create account, chat about merch, see matching items appear on the page and get honest answers about price and stock from a local database

do not do anything yet just try to understand what i tell there's more for the scenario
```

```
i will give you the campus_customs.db with tables for the product catalogue, inventory by size and users (with hashed passwords). Product image file paths are in the catalogue table. research yalebulldogblue.com to learn the style of campus customs page and information for your agent prompt.

remember to use portkey_api_key witht he model i used before but let me know if u ever need a stronger model

work one problem that i'm gonna tell u at a time just like previous homework. in the end push the project to a public github repo so i can submit the repo url

these are the data they will contains
- data/campus_customs.db an sqlite database with tables catalogue, inventory and users (there's one test user)
- data/products/ - product images; paths match the catalogue table
process this then wait for more instruction on my next 13 problems
@/Users/pinkpawika/Downloads/data-2
```

```
problem 1 is called vibe code prompts
i want u to create AI_prompts.md at the start of the assignment and keep it updated as you work. this file is the log of what you typed to you

put one section for each problem. each section must include the following:
- the problem number and title
- prompts i type (including the follow up prompt if needed)
the running site, database writes and screenshot will be the evidence
```

**What was lacking:** The first prompt only said this was homework 4. The shop, the React + Vite + TypeScript front end, the FastAPI back end, the PydanticAI agent, accounts, on-page product matches, honest price and stock from the local database, Portkey / gpt-5.6-lunar, one problem at a time, the public GitHub repo, the data folders, and that this step is the prompt log all came in later prompts.

---

## Problem 2: Analyze the database

**Prompt I typed in**

```
next is problem 2: analyze the database

i want u to look at the database data/campus_customs.db and understand the fields of each table
especially catalogue, inventory, and users but u should understand all lists out the fields and definition for me to check first
then start the file output/harness.md and write down each table and its fields and one short line on why each fields matters for the shop or the chatbot.

you will keep growing this harness file in later problems with models, tools, safety, specs
```

**Follow-up prompts**

```
if empty leaves it as empty 
for hoodie and pull over  as well as thsirt lets treat them as the same thing
```

---

## Problem 3: Build the Campus Customs website

Worth 10 points.

**Prompt I typed in**

```
ok lets do problem 3 called build the campus customs website this worth 10 points pls be careful i'll type the instruction next
```

**Follow-up prompts**

```
i want you to scaffold a react + vite + typescript frontend for campus customs. Put a nav bar at the top that links to the main pages:
- home
- products
- about us
- log in
- create account

use campus customs style wording and theme from yalebulldogblue.com for home and about us, but write these pages in your own voice (my voice if u can) do nnot copy original site text
more instructions to come
```

```
on the product page, show product images from the calalog (use the image paths in the database) with basic product infor e..g name price short description

make each product open a single item page with large image on one side, full product text on the other with description,price, sizes, stocks (if u have) if no stocks (when it is zero) then have a badge sold out. clicking a card on products should take the shopper there.

add a chart interface in the bottom right of the site (a floating chat panel is fine) but makes it beautiful. it doesn't need to talk to an agent - a stub that will call the BE later is enough for this problem

you will need a small API soon to read the database, fine to start a simple fastapi app in backend/main.py just to serve products and images then grow it into the agent backend in next problem (5)
```

---

## Problem 4: Create account and login

**Prompt I typed in**

```
ok let's do problem 4 : createa ccount and login

i want you to build a normal create-account / login flow
- create account with input like firstname, lastname, email, password
(check format for email) and all are mandatory
- then log in: input as email and password that must matched the created one

the new accounts will go to users table, make sure passwords are stored securely so hackers both human and it cannot access

the seed database already has a test user you can use while bulding
then confirm log in as a that user and that a brand new account that created also works

update output/harness.md with how auth works make sure passwords are protected
```

**Follow-up prompts**

```
saved first i'll come back later to finish the work
```

---

## Problem 5

**Prompt I typed in**

```
i'm back let's do problem 5
```

**Follow-up prompts**

```
problem 5 is called pydanticAI agent backend

i want u to build the shop chatbot as a pydanticAI agent behind FastAPI plugged in to the front end chat widget. put the api app in backend/main.py this will be the file i run with uvicorn. keep the agent as these four files next to it (same idea as hw 3)
- backend/prompts/prompt.md - system prompt (grow this same file later)
- backend/agent.py - agent entry / wiring
- backend/tools.py - tools the agent can call
- backend/models.py - pydantic or pydancticAI structured types
In main.py expose a chat route so a message from the website returns a reply from the agent (and whtever else u need for product/auth) you will need ai model api key for the agent lmk if u need anythig

i also want u to put campus customs voice and safety basics in to prompts/prompt.md (but let me review first) which i will expand tools and safety later. start or update types in model.py for chat replies or product cards as needed. 

in output/harness.md note how the front end talks to fastAPI and how the agent is loaded (prompt file + model)

make sure the backend runs from the backend/ folder like this
uvicorn main:app --reload --port 8000
```

```
ok you can add them and then we'll do problem 6
```

---

## Problem 6: Tools: product info and stock

**Prompt I typed in**

```
problem 6 :  tools: product info and stock
i want u to create agent or give them tools that look up real information from campus_customs.db
- product description
- price
- how many are in stocks (by size when the customer asks)
the agent must use the database do not invent prices or quantities, if a size is out of stock just say so clearly

expand prompt/prompt.md so the agent knows to call these tools for price and stock questions add or update return types in models.py

in output/harness,md list each tool and explain which model fields you chose for lookup results and why
```

---

## Problem 7: Chat search that updates the page

**Prompt I typed in**

```
ok let's do problem 7: chat search that updates the page
i want to add a neat beautiful but simple feature to the site. when customer asks about a type of items e.g. what hoodies do you have the agent should search for the catalog and the website should dynamically show those matching items as a product cards including image name price short info (make sure UI is simple and good UX)

this is an api contract: the agent returns structured product matches and then the front end renders them on the website. 

After the dynamic product cards are loaded by the new feature, make sure the same single item page behavior built in problem 3 still work: each rpoduct card includingt he ones the chat just put ont he page should still open that detail view including large image and full info when clicked.

update prompts/@backend/prompts/prompt.md and outout.harness.md so it is clear how search resylts reach the page
```

---

## Problem 8: Customer memory

**Prompt I typed in**

```
ok let's do problem 8 is called customer memory

whhen a shopper is logged in save their chat hisotry in the database in an appropriate table and relaoad it when they return, the agent should know the followung
- who is chatting including the name and email 
put that in agent deps or an equivalent clear pattern and/or tools the agent can call

also pass enough page context that if someone is on a product page and asks do u have this in pink the agent knows which item they mean (can put code into agent context) -  if u dont understand ask me

guests can still chat but history only needs to persist for logged in users document in output/harness.md how user chat history is stored what customer fields the agent sees and how page context is passed
```

---

## Problem 9: Usability improvements

**Prompt I typed in**

```
ok lets do next problem 9: usability improvements

now that the core shop works, improve it, choose and implement
1. 2 front end usability improvements, make site look better and easier
2. agent/backend usability improvements to make the agent output better, more accurate or safer
these improvement can be new agent tools or things that make the agent run faster or cheaper
Write output/usability.md before or as you build, for each improvement say
- what u added
- why it helps campus customs shopper or the business

then make sure all improvements actually shpw up int he running app. graders will read the wrtite up and look for the feature u got to do this right
```

---

## Problem 10: Style the website

**Prompt I typed in**

```
ok now problem 10: style the website
- add creative design so the site feels like a real campus customs store front, fonts, color, hierarchy

the more creativity u are the more points i'll get

write output/design.md  waht you changed and why it should help customers sticks around and buy, keep it concrete and short
```

---

## Problem 11: Site testing (app check)

**Prompt I typed in**

```
problem 11: site testing (app check)

test the live site and document it in output/app_check.htmk (a page i can double-click open) include clear screenshots and short captions for
1. chat checking the inventory level of an item (honest stock/price from the db)
2. the dynamic search-results cards appearing after a categoty question (e.g. hoodies)
3. one of the usability features you added in problem 9

amke the html easy to grade: heading for each check screenshot, one or two sentences on what the screenshot proves put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths (e.g. app_check_images/inventory.png)
```

---

## Problem 12: Audit trail, safety, finish harness

**Prompt I typed in**

```
problem 12: audit trail, safety, finish harness

keep an append-only output/audit_trail.json of agent loop activity (time, tool name, short args/result, stop reason). do not wipe it between runs

also think of some safety rules to give the agent and put them in prompts/prompt.md

finish output/harness.md so it is clear how the system works 
- model fields in models.py and why u chose them
- tools and abilities
- safety rules
- specs (loop limits, result caps, models, how to run front+back)
```

---

## Problem 13: Push to GitHub and submit the URL

**Prompt I typed in**

```
problem 13: push to github and submit the url

put the code in a folder name hw4 and push it to a public GitHub repository.   then send me the repo URL (the link that grader can grade)  do not put real .env, campus_customs.db or product images in the github repo. use .gitignore include .env.example with placeholders only  expected file layout as follows  local only data pack (not in git)  the agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py and models.py  README.md should explain how to run the front end and backend after placing the data pack
```
