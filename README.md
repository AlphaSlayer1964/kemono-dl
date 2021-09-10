# Kemono.party-Downloader
This is a quick and dirty kemono.party downloader using python.
You will need to install bs4 by using the command "pip install bs4".
Ypu will aslo need to chnage the Download_Location variable at the top and all four of the cookie values for kemonoparty.
You can get the cookie values from using a chrome or firefox extention.
They are needed so requests can get past their ddos protection.
Then place the users main page link in the Users.txt file (one user per line).
links should look like: https://kemono.party/patreon/user/*******

WARNINGS!
If you stop the script while it is downloading what ever file was last being downloaded will probably be broken and skipped next time.
Also you might get IP banned from kemono party if you use it a lot (though this has not happened to me and I've used this script a lot in testing and actual use just be warned)
If the site changes the script might break.
Just notieced some files can be none kemono hosted so they probably won't downlaod (example youtube links)
Also noticed some "download able files" are not even real files so will need to look into that???

TO DO:
[COMPLETED] Instead of skipping files based on if a file of the same name exists change to be based on a log file with all saved posts id's recoreded in it.
Intigrate youtube-dl for downloading videos?
Create a links.txt file to hold all embeded links in content section.
Need to look into duplicate names for files and downloads
Figure out how to format readme lol!
