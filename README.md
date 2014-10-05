# Controlio

Controlio is a simple service which allows you to control your computer via SMS **and voice**. With one simple registration step, you not longer have to be bound to your clunkly machine for on-the-go operations. No more running out of the house, only to remember you forgot to do something on your computer!

## Web Server

This is the web server that acts as the middleman between Twillio and a local Controlio client. For more details about the client, please see the [controlio repo](https://github.com/Controlio/controlio).

## Setup

You can either run your own web instance, or use the one at http://ym-remote-control-web.herokuapp.com/. Register with your phone number, and pick a password. You'll be given an API key, which you should save in a plain text file at `~/.remote_control_key`. After that, check out the [controlio repo](https://github.com/Controlio/controlio) to get your local client up and running.
