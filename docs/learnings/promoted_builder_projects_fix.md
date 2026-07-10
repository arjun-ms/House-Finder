Here is exactly what happened and why it changed:

Originally, we just typed "Whitefield" and it searched that one specific area. But you mentioned you needed the data from the other dropdown variations too (like Whitefield Hoskote Road and Whitefield Main Road).
 
We initially tried to select all of those checkboxes from the dropdown at the exact same time to do one massive, combined search.

What happened then: By combining three massive areas into a single search, MagicBricks' algorithm flooded the results feed with over 300+ "Promoted Builder Projects." It treated the massive search radius as a signal to show you generic project ads, completely burying the actual, individual flats we wanted to scrape.

How we fixed it: To bypass that ocean of spam but still get you the data for all the locations,we made the bot type and search them one at a time. It types "Whitefield" and scrapes the real flats. Then it types "Whitefield Hoskote Road", scrapes those real flats, and so on.

Right now, I am finishing the final update so that you don't even have to hardcode those variations in the script. You just configure  "Whitefield"  once, and the bot will dynamically read the dropdown, extract the variations it finds, and loop through them automatically!