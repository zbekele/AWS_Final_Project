from flask import Flask, render_template, request, redirect, jsonify, url_for, flash  # noqa
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database_setup import Base, Category, Item, User
from flask import session as login_session
from flask_oauthlib.client import OAuth
import random
import string

# --------------IMPORTS FOR THIS STEP---------------
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# -------------- Connect to Database and create database session ----

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:\
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():

        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    print(access_token)
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.

        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # token given is invalid
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# JSON APIs to view Restaurant Information


@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    items = session.query(Item).all()
    return jsonify(
        Categories=[category.serialize for category in categories],
        Items=[item.serialize for item in items])


@app.route('/catalog/<int:category_id>/<int:item_id>/JSON/')
def itemDetailsJSON(category_id, item_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        item = session.query(Item).filter_by(id=item_id).one()
        return jsonify(
            Category=category.serialize,
            Item=item.serialize)
    except SQLAlchemyError:
        return ("Item is not found!!!")


# Show all categories and latest items
@app.route('/')
@app.route('/showCatalog/')
def showCatalog():
    categories = session.query(Category).order_by(asc(Category.name))
    latestItems = session.query(Item).order_by(Item.created.desc())
    return render_template(
        'catalog.html',
        categories=categories,
        latestItems=latestItems)

# Show all items in a specific category


@app.route('/catalog/<int:category_id>/items')
def showItems(category_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        items = session.query(Item).filter_by(category_id=category_id).all()
        return render_template('items.html', items=items, category=category)
    except SQLAlchemyError:
        return ("Category is not found!!!")


# Show an items's details
@app.route('/catalog/<int:category_id>/<int:item_id>')
def itemDetails(category_id, item_id):
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        item = session.query(Item).filter_by(id=item_id).one()
        return render_template('item.html', item=item, category=category)
    except SQLAlchemyError:
        return ("Item is not found!!!")


# Add a new item
@app.route('/catalog/items/new', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')

    categories = session.query(Category).order_by(asc(Category.name))
    user_id = login_session['user_id']

    if request.method == 'POST':
        category = session.query(Category).filter_by(
            name=request.form['category']).one()
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=category.id,
            user_id=user_id)
        session.add(newItem)
        session.commit()
        flash('New Item -  %s  Successfully Created' % (newItem.name))
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newitem.html', categories=categories)

# Edit an item


@app.route('/catalog/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    item = session.query(Item).filter_by(id=item_id).one()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() \
        {alert('You are not authorized to edit other users' \
        items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            category = session.query(Category).filter_by(
                name=request.form['category']).one()
            item.name = request.form['name']
            item.description = request.form['description']
            item.price = request.form['price']

            item.category_id = category.id
            flash('%s Successfully Edited' % item.name)
            return redirect(url_for('showItems', category_id=item.category.id))
    else:
        return render_template(
            'edititem.html',
            categories=categories,
            item=item)


# Delete an item
@app.route('/catalog/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(id=item_id).one()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() \
        {alert('You are not authorized to delete other users'\
         items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item)
        flash('%s Successfully Deleted' % item.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteitem.html', item=item)

# Add a new category


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    user_id = login_session['user_id']
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'], user_id=user_id)
        session.add(newCategory)
        session.commit()
        flash('New Category %s Successfully Created' % (newCategory.name))
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newcategory.html')


# Edit a category
@app.route('/catalog/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() \
        {alert('You are not authorized to edit other users'\
         categories.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            flash('%s Successfully Edited' % category.name)
            return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('editCategory.html', category=category)


# Delete a category and all of the items associated with it
@app.route(
    '/catalog/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() \
        {alert('You are not authorized to delete other users' \
        categories.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        for item in items:
            session.delete(item)
        session.delete(category)
        flash('%s Category and All Items Associated with this \
            Category Successfully Deleted' % category.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category=category)


# Disconnect based on provider
@app.route('/disconnect/')
def disconnect():
    print(login_session)
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            if 'gplus_id' in login_session:
                del login_session['gplus_id']
            if 'credentials' in login_session:
                del login_session['credentials']
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.", 'success')
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in", 'danger')
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='localhost', port=5000)
