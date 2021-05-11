from flask import Flask,render_template,redirect,request,url_for,flash,session,logging
from flask_mysqldb import MySQL
from wtforms import *
from functools import wraps
from datetime import datetime

app = Flask(__name__)

#CONFIG MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'BookADDA'  #Database name for MYSQL
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)

now = datetime.now()
create_date = now.strftime("%Y-%m-%d %H:%M:%S")


#CHECK IF USER IS LOGGED IN
def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorized, Please login','danger')
			return redirect(url_for('login'))
	return wrap

@app.route('/home')
def home():
	return render_template('home.html')


#REGISTER FORM 
class RegisterForm(Form):
	name = StringField('Name',[validators.Length(min=1, max=100)])
	roll = IntegerField('Roll',[validators.NumberRange(min=0, max=40000)])
	branch = StringField('Branch',[validators.Length(min=2, max=50)])
	sem = IntegerField('Semester',[validators.NumberRange(min=1, max=8)])
	email = StringField('Email',[validators.Length(min=6, max=50)])
	contact = StringField('Contact',[validators.Length(min=1, max=100)])
	password = StringField('Password',[
			validators.DataRequired(),
			validators.EqualTo('confirm',message='Password do not match')
		])
	confirm = PasswordField('Confirm Password')


@app.route('/register',methods=['GET','POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = request.form.get("name")
		roll = request.form.get("roll")
		branch = request.form.get("branch")
		sem = request.form.get("sem")
		contact = request.form.get("contact")
		email = request.form.get("email")
		password = request.form.get("password")
		confirm = request.form.get("confirm")

		if(password == confirm):
			#Create cursor
			cur = mysql.connection.cursor()

			cur.execute("insert into buyer(B_id,B_name,B_password,B_branch,B_sem,B_email,B_contact) values(%s,%s,%s,%s,%s,%s,%s)",(roll,name,password,branch,sem,email,contact))

			#COMMIT TO DB
			mysql.connection.commit()

			#CLOSE CONNECTION
			cur.close()
			flash('You have successfully registered','success')

			return redirect(url_for('login'))

		else:
			error = 'Both the passwords are not matching'
			return redirect(url_for('register'),error=error)

	return render_template('register.html', form=form)


@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		#GET FORM FIELDS
		email = request.form.get("email")
		password_check = request.form.get("password")

		#CREATE CURSOR
		cur = mysql.connection.cursor()

		#GET USER BY USERNAME
		result = cur.execute("select * from buyer where B_email = %s",[email])

		if result > 0:
			data = cur.fetchone()
			password = data.get("B_password")
			name = data.get("B_name")

			#COMPARE PASSWORDS 
			if (password_check == password):
				session['logged_in'] = True
				session['name'] = name

				flash('You are now logged in','success')

				return redirect(url_for('welcome'))
			else:
				error = 'Invalid Login credentials'
				return render_template('login.html',error=error)

			#CLOSE CONNECTION
			cur.close()
			
		else:
			error = 'No User Found'
			return render_template('login.html',error=error)

	return render_template('login.html')


@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))


@app.route('/cart')
@is_logged_in
def cart():
	if 'name' in session:
		name = session['name']

	cur = mysql.connection.cursor()
	total = 0

	result1 = cur.execute("select * from buyer where B_name = %s",[name])
	profile = cur.fetchone()
	b_id = profile.get("B_id")

	cart = cur.execute("select * from cart where B_id = %s",[b_id])
	if cart > 0:
		info = cur.fetchone()
		c_id = info.get("C_id")
		app.logger.info(c_id)
	else:
		cur.execute("insert into cart(B_id) values(%s)",[b_id])
		cart = cur.execute("select * from cart where B_id = %s",[b_id])
		info = cur.fetchone()
		c_id = info.get("C_id")

	mysql.connection.commit()

	result = cur.execute("select * from item where C_id = %s",[c_id])
	item = cur.fetchall()
	if len(item) > 0:
		book_list = []
		for row in item:
			book_id = row.get("Book_id")
			result = cur.execute("select * from book where Book_id = %s",[book_id])
			data = cur.fetchone()
			a_id = data.get("Author_id")
			p_id = data.get("P_id")
			e_id = data.get("Edition_id")

			result2 = cur.execute("select * from book where Book_id = %s",[book_id])
			book = cur.fetchone()
			price = book.get("Price")
			total += price
			
			result4 = cur.execute("select * from author where Author_id = %s",[a_id])
			author = cur.fetchone()

			result5 = cur.execute("select * from publisher where P_id = %s",[p_id])
			publisher = cur.fetchone()

			result6 = cur.execute("select * from edition where Edition_id = %s",[e_id])
			edition = cur.fetchone()

			result7 = cur.execute("select * from item where C_id = %s",[c_id])
			product = cur.fetchone()

			book_list.append({
				'Item_id':product['Item_id'],
				'Book_name':book['Book_name'],
				'Price':book['Price'],
				'Author':author['Author'],
				'Publisher':publisher['Publisher'],
				'Edition':edition['Edition']
			})
		
		cur.execute("update cart set total_price = %s where C_id = %s",(total,c_id))
		mysql.connection.commit()

		return render_template('cart.html',cart=book_list,total=total)

	cur.close()
	return render_template('cart.html')


@app.route('/welcome',methods=['GET','POST'])
@is_logged_in
def welcome():
	if 'name' in session:
		name = session['name']

	cur = mysql.connection.cursor()

	result1 = cur.execute("select * from buyer where B_name = %s",[name])
	if result1 > 0:
		profile = cur.fetchone()
		s_id = profile.get("B_id")

	result2 = cur.execute("select * from book where S_id != %s",[s_id])
	if result2 > 0:
		booklist = cur.fetchall()

		result3 = cur.execute("select * from author")
		author = cur.fetchall()
		result4 = cur.execute("select * from publisher")
		publisher = cur.fetchall()
		result5 = cur.execute("select * from edition")
		edition = cur.fetchall()

		if request.method == 'POST':
			filters = request.form.getlist('books')
			print(filters)

		return render_template('content.html',booklist=booklist,author=author,publisher=publisher,edition=edition)

	cur.close()
	return render_template('content.html')


@app.route('/product_details/<string:Book_id>/',methods=['GET','POST'])
@is_logged_in
def product_details(Book_id):
	cur = mysql.connection.cursor()

	if request.method == 'POST':
		if 'name' in session:
			name = session['name']

		result = cur.execute("select * from buyer where B_name = %s",[name])
		profile = cur.fetchone()
		b_id = profile.get("B_id")
		result = cur.execute("select * from cart where B_id = %s",[b_id])
		cart = cur.fetchone()
		c_id = cart.get("C_id")

		app.logger.info(c_id)

		check = cur.execute("select * from item where Book_id = %s and C_id = %s",(Book_id,c_id))
		if check == 0:
			cur.execute("insert into item(Book_id,C_id) values(%s,%s)",(Book_id,c_id))
			flash('Product added to cart','success')
		else:
			flash('You have already added this product','success')

		mysql.connection.commit()

	result = cur.execute("select * from book where Book_id = %s",[Book_id])
	if result > 0:
		info = cur.fetchall()
		details = []
		for row in info:
			s_id = row.get("S_id")
			a_id = row.get("Author_id")
			p_id = row.get("P_id")
			e_id = row.get("Edition_id")

			result1 = cur.execute("select * from seller where S_id = %s",[s_id])
			seller = cur.fetchone()
			
			result2 = cur.execute("select * from author where Author_id = %s",[a_id])
			author = cur.fetchone()

			result3 = cur.execute("select * from publisher where P_id = %s",[p_id])
			publisher = cur.fetchone()

			result4 = cur.execute("select * from edition where Edition_id = %s",[e_id])
			edition = cur.fetchone()

			result5 = cur.execute("select * from book where Book_id = %s",[Book_id])
			book = cur.fetchone()

			details = [{
				'S_name':seller['S_name'],
				'S_branch':seller['S_branch'],
				'S_sem':seller['S_sem'],
				'Category':book['Category'],
				'Book_name':book['Book_name'],
				'Price':book['Price'],
				'Author':author['Author'],
				'Publisher':publisher['Publisher'],
				'Edition':edition['Edition'],
				'Description':book['Description'],
				'S_email':seller['S_email']
			}]

		return render_template('product_details.html', product=details)
	
	
	cur.close()
	return render_template('product_details.html')


@app.route('/profile')
@is_logged_in
def profile():
	if 'name' in session:
		name = session['name']

	cur = mysql.connection.cursor()

	result = cur.execute("select * from seller where S_name = %s",[name])
	if result > 0:
		profile = cur.fetchall()
		for row in profile:
			s_id = row.get("S_id")

	result = cur.execute("select * from buyer where B_name = %s",[name])
	buyer = cur.fetchone()
	b_id = buyer.get("B_id")

	result1 = cur.execute("select * from book where S_id = %s",[s_id])
	booksold = cur.fetchall()
	result2 = cur.execute("select * from order_details where B_id = %s",[b_id])
	orders = cur.fetchall()
	
	cur.close()

	return render_template('profile.html',profile=profile,booksold=booksold,orders=orders)

	

#PRODUCT FORM
class BookForm(Form):
	title = StringField('Title',[validators.Length(min=1, max=100)])
	author = StringField('Author',[validators.Length(min=1, max=100)])
	publisher = StringField('Publisher',[validators.Length(min=1, max=100)])
	sem = IntegerField('Semester',[validators.NumberRange(min=1, max=8)])
	edition = IntegerField('Edition')
	category = SelectField('Publisher',choices=[('PDF','PDF'),('Books','Books')])
	price = FloatField('Price')
	description = StringField('Description',[validators.Length(min=1,max=200)])


@app.route('/product_form',methods=['GET','POST'])
@is_logged_in
def product_form():
	form = BookForm(request.form)
	if request.method == 'POST' and form.validate():
		title = request.form.get("title")
		sem = request.form.get("semester")
		author = request.form.get("author")
		publisher = request.form.get("publisher")
		edition = request.form.get("edition")
		category = request.form.get("category")
		price = request.form.get("price")
		description = request.form.get("description")

		cur = mysql.connection.cursor()

		#CHECK IF AUTHOR IS ALREADY PRESENT
		result1 = cur.execute("select * from author where Author = %s",[author])
		if result1 > 0:
			data1 = cur.fetchone()
		else:
			cur.execute("insert into author(Author) values(%s)",[author])

		#CHECK IF PUBLISHER IS ALREADY PRESENT
		result2 = cur.execute("select * from publisher where Publisher = %s",[publisher])
		if result2 > 0:
			data2 = cur.fetchone()
		else:
			cur.execute("insert into publisher(Publisher) values(%s)",[publisher])

		#CHECK IF EDITION IS ALREADY PRESENT
		result3 = cur.execute("select * from edition where Edition = %s",[edition])
		if result3 > 0:
			data3 = cur.fetchone()
		else:
			cur.execute("insert into edition(Edition) values(%s)",[edition])

		#GETTING ID FOR EACH TABLES
		if 'name' in session:
			name = session['name']
		result = cur.execute("select * from buyer where B_name = %s",[name])
		profile = cur.fetchone()
		s_id = profile.get("B_id") 

		result1 = cur.execute("select * from author where Author = %s",[author])
		data1 = cur.fetchone()
		a_id = data1.get("Author_id")

		result2 = cur.execute("select * from publisher where Publisher = %s",[publisher])
		data2 = cur.fetchone()
		p_id = data2.get("P_id")

		result3 = cur.execute("select * from edition where Edition = %s",[edition])
		data3 = cur.fetchone()
		e_id = data3.get("Edition_id")

		#INSERTING RECORD IN BOOK TABLE
		cur.execute("insert into book(Book_name,Book_sem,Category,Price,Description,S_id,Author_id,P_id,Edition_id) values(%s,%s,%s,%s,%s,%s,%s,%s)",(title,sem,category,price,description,s_id,a_id,p_id,e_id))
		
		#COMMIT AND CLOSE
		mysql.connection.commit()
		cur.close()
		return redirect(url_for('welcome'))

	return render_template('product_form.html',form=form)


@app.route('/update_form/<string:Book_id>/',methods=['GET','POST'])
@is_logged_in
def update_form(Book_id):
	form = BookForm(request.form)
	if 'name' in session:
		name = session['name']

	cur = mysql.connection.cursor()

	result = cur.execute("select * from seller where S_name = %s",[name])
	profile = cur.fetchone()
	s_id = profile.get("S_id") 

	result1 = cur.execute("select * from book where Book_id = %s and S_id = %s",(Book_id,s_id))
	if result1 > 0:
		update = cur.fetchall()
		for row in update:
			a_id = row.get("Author_id")
			p_id = row.get("P_id")
			e_id = row.get("Edition_id")
			
			result2 = cur.execute("select * from author where Author_id = %s",[a_id])
			author = cur.fetchall()

			result3 = cur.execute("select * from publisher where P_id = %s",[p_id])
			publisher = cur.fetchall()

			result4 = cur.execute("select * from edition where Edition_id = %s",[e_id])
			edition = cur.fetchall()

		if request.method == 'POST':
			title = request.form.get("title")
			sem = request.form.get("semester")
			author = request.form.get("author")
			publisher = request.form.get("publisher")
			edition = request.form.get("edition")
			category = request.form.get("category")
			price = request.form.get("price")
			description = request.form.get("description")

			result5 = cur.execute("select * from author where Author = %s",[author])
			if result5 > 0:
				author = cur.fetchone()
				a_id = author.get("Author_id")
			else:
				cur.execute("insert into author(Author) values(%s)",[author])
				result5 = cur.execute("select * from author where Author = %s",[author])
				author = cur.fetchone()
				a_id = author.get("Author_id")

			result6 = cur.execute("select * from publisher where Publisher = %s",[publisher])
			if result6 > 0:
				publisher = cur.fetchone()
				p_id = publisher.get("P_id")
			else:
				cur.execute("insert into publisher(Publisher) values(%s)",[publisher])
				result6 = cur.execute("select * from publisher where Publisher = %s",[publisher])
				publisher = cur.fetchone()
				p_id = publisher.get("P_id")


			result7 = cur.execute("select * from edition where Edition = %s",[edition])
			if result7 > 0:	
				edition = cur.fetchone()
				e_id = edition.get("Edition_id")
			else:
				cur.execute("insert into edition(Edition) values(%s)",[edition])
				result7 = cur.execute("select * from edition where Edition = %s",[edition])
				edition = cur.fetchone()
				e_id = edition.get("Edition_id")


			cur.execute("update book set Book_name = %s,Book_sem = %s,Price = %s,Category = %s,Author_id = %s,P_id = %s,Edition_id = %s,Description = %s,date = %s where Book_id = %s",(title,sem,price,category,a_id,p_id,e_id,description,create_date,Book_id))

			mysql.connection.commit()
			return redirect(url_for('profile'))
		
		return render_template('update_form.html',update=update,author=author,publisher=publisher,edition=edition)
	cur.close()

	return render_template('update_form.html')


@app.route('/delete_item/<string:Item_id>/',methods=['POST'])
@is_logged_in
def delete_item(Item_id):
	cur = mysql.connection.cursor()
	
	cur.execute("delete from item where Item_id = %s",[Item_id])

	mysql.connection.commit()
	cur.close()
	return redirect(url_for('cart'))


@app.route('/transaction')
@is_logged_in
def transaction():
	if 'name' in session:
		name = session['name']

	cur = mysql.connection.cursor()

	result = cur.execute("select * from buyer where B_name = %s",[name])
	profile = cur.fetchone()
	b_id = profile.get("B_id")
	result = cur.execute("select * from cart where B_id = %s",[b_id])
	cart = cur.fetchone()
	total_price = cart.get("total_price")
	c_id = cart.get("C_id")
	
	check = cur.execute("select * from item where C_id = %s",[c_id])
	if check > 0:
		books = cur.fetchall()
		for row in books:
			print(row)
			book_id = row.get("Book_id")
			get_info = cur.execute("select * from book where Book_id = %s",[book_id])
			book_info = cur.fetchone()

			title = book_info.get("Book_name")
			category = book_info.get("Category")
			price = book_info.get("Price")
			semester = book_info.get("Book_sem")
			seller_id = book_info.get("S_id")
			author_id = book_info.get("Author_id")
			publisher_id = book_info.get("P_id")
			edition_id = book_info.get("Edition_id")
			description = book_info.get("Description")

			cur.execute("insert into order_details(Book_name,Category,Price,Description,Book_sem,S_id,B_id,Author_id,P_id,Edition_id,sold_date) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(title,category,price,description,semester,seller_id,b_id,author_id,publisher_id,edition_id,create_date))

			mysql.connection.commit()
		return render_template('transaction.html',total=total_price)

	return render_template('transaction.html',total=total_price)


@app.route('/receipt')
@is_logged_in
def receipt():

	return render_template('receipt.html')



if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)