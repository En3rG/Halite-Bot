# Halite-Bot
Two Sigma's <a href="https://halite.io/">Halite</a> competition ending on Feb 12,2017. Finished as rank 23 out of 1592 (Diamond Tier) 

# Summary
I heard about Halite from a coworker, it sounded pretty interesting so I decided to give it a shot.  I downloaded the python starter package and began messing around with it.  I wanted to make up my own strategies so I avoided reading the forums.  My coworker then gave me the overkill bot and that owned my initial bot.  I was suprised how well the overkill bot was doing with only 50 lines of code.  The goal then became to just over power the overkill bot.  From there on I pretty much got addicted to Halite.

# Bot Summary
Here's a quick summary of my bot

* Initialization

I had this commented out with my final submission since it was timing out during the last day, but that was really due to the server issues they were having because everyone were submitting their bots.  This basically get the highest 11 squares (up to 14) that will yield the highest production/strength ratio from the starting square.  I then had two options, whether to tunnel through these 11 squares with all my units or just have the minimum strength required.  For example, if I currently have 5 squares and combining 3 of the squares will be enough to take the 6th square, then the remaining 2 squares will be used to expand somewhere else.

* Attack/Defend

The attack portion is base on the neutrals that are in the front line.  These are squares that have 0 strength and is between my squares and the enemies.  It iterates through each of the neutral squares in front line and numbers my squares adjacent to it, up to whatever the variable is set to.  My final submission was set to 6.  Basically, my square right next to the neutral square is numbered as '1', the ones next to this square is numbered '2' and so on up to 6.  This makes each of the numbered squares to flow towards the lower number all the way to the original neutral front line square.  This can cause a build up, since every one of them are just going into a single square, so I added an option where a specified number will be allowed to create another opening.  In my final submission, this number was set to 3.  So if my square that is numbered '3' met the required strength and is next to a neutral, it'll take that neutral square and basically make that a new opening towards the enemy.  This help prevent some build up.
* Expand
* Evade
* Middle squares
* Manage
