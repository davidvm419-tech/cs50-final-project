# Chicake webpage 
#### Video Demo: <>

#### Description: I created a webpage for a friend who makes desserts as an entepreneur, she uses only WhatsApp and I believe that it could be improved upon in the future. The webpage is in Spanish because we are from Colombia.

[!WARNING]
## Disclaimer: 
all images logos and descriptions for the products are the property of my friend Carolina who provided them so this project could be possible. 

### Background
As I am from Colombia, we still need to adopt a lot of technologies to improve our work and our productivity. In addition I like web development and I am going to focus on that area. Based on that the idea to develop of a simple web application and to improve upon that was born. This is the first step in that direction.

### Toolkit
To create this web application I used, mainly, Python, HTML, jinja, Bootstrap, CSS, Flask and SQL. In addition I created everything outside CS50 Codespace so I could take off my training wheels a bit more. I used MJicrosoft Copilot as a teacher, pretty much in the same spirit as the rubber duck debugger, Flask documentation and W3School as helpers when I encountered bugs and syntax errors. 

### HTML
HTML is the skeleton of the page, I used it to create many of templates for different renders and user interactions. The template layout is the heart of the HTML structure and where logged-in users can see some features and guests users can see other. 3leches, cheescake, cupcakes, otros, register, login and homepage are the templates that all users will see. Meanwhile logged-in users will see: userhomepage, orders, history and password_update in addition of the previous templates.

## Static
In this folder there are styles for CSS personalization on colors, fonts, backgrounds, the overall style of the webpage. Moreover, this folder contains all the images that are displayed in the different HTML templates.

# SQL
The database.db is the databse created for this project, and it includes four tables. The users table stores user information such as username, a password hash, phone and an id column.
The products table stores current product information such as name, type, price and an id column.
The temp_orders table stores the user id (referenced from users table), product name, quantity, type, price, date and an id column.
And the users_orders table stores that stores the same information as temp_orders.

## Features and functionality
There are two Python documents, helpers.py and app.py. In helpers there are two functions, login_requiered thats a reintroduction of the function used in finance problem set to guarantee that logged-in users can see the corresponding templates. The second is password_check, which is an implementation I created to verify that users create a password that meets the required criteria.

The full implementation of the application is in app.py. First it includes the set up of the Flask application followed by the database configuration used to retrieve and store information. After that, there are functions that handle the functionality of the different templates. Let's go through it function by function:

home: This function checks whether the user is logged in. If they are, it renders the userhomepage template along with their most recent order; if the user has no orders, it displays a message indicating that no purchases have been made. If the user is not logged in, it renders the guest homepage.

-register: This function handle the registration process. First it checks if the corresponding fields are empty and ensure that register a valid phone number via POST method.
Second it checks the database for an existing username or phone number to ensure that there are not duplicated registrations.
Third it checks that password  meets the requered criteria via password_check. If it passes, the function then verifies that the password and confirmation match. Finally, it hashes the password using generate_password_hash.
Fourth it inserts the information into the users table, saves the user session using the user id and redirects to user homepage.
If any of the steeps fail, it renders the register template.

-login: This functon handle the login process. First it checks if the corresponding fields are empty via POST method. 
Second it query the database for a valid username or phone (since both can be use to log in) and for the correct password. Finally, saves the user session using the user id and redirects to user homepage. it If any of the steeps fail, it renders the login template.

-logout: this function logs out the user by clearing the session and then redirects to homepage.

-orders: This functon handle the entire orders creation and purchase. First, it retrieves the products and their types from the database to display them in the HTML using a selector tag.
Second, it uses the temp_orders table to temporarily store orders that have not been checked out. The user has 5 minutes to complete the checkout; otherwise, the information in the table is deleted. This ensures that the HTML table appears empty if the user does not complete the purchase within the 5‑minute limit. After that check, all the necessary failsafes are applied to ensure that the user selects a valid product with a valid type. If the user makes a mistake during the process, a flash message will guide them. When the process is succesfull, the information is inserted into temp_orders table and then displayed in the HTML as a table at the bottom. This table shows the current products in the order, including each price and the total price (shown in Colombian pesos).
Third, if the user is ready to check out and presses the “Realizar compra” button, the information is inserted into the users_orders table, deleted from temp_orders, the user is redirected to the userhomepage, where the most recent purchase is displayed in the HTML.
If something fails during the order creation process, the function renders the orders template again. It also always queries the temp_orders table to ensure that the user sees a valid order on every reload.

-history: This function handles the user’s purchase history. It queries the users_orders table to display all orders (from newest to oldest), and to prevent the table from growing indefinitely, it limits the display to 10 rows. If the user has not made any purchases, it displays a corresponding message.

-password_update: It handle that users can update their password. First it clears the session to ensure safety. Second, checks if the corresponding fields are empty via POST method. 
Third it query the database for a valid username or phone (since both can be use to change password)  and verifies the user’s current password. 
Fourth it checks that the new password meets the requered criteria via password_check. If it passes, the function then verifies that the new password and its confirmation match. Next, it hashes the new password using generate_password_hash.
Fifth, it updates the hashed password in the users table, restores the user session using the user id, and redirects the user to the homepage. If any of the steps fail, it renders the password update template.

-routes to products: These routes direct guest users to the different product sections.

## Final thoughts
This is how my "Chicake" webpage works under the hood. It’s not perfect yet, and I’ll continue improving it along the way to turn it into a fully functional webpage that can be used in the real world.







