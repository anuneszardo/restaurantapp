# -*- coding: utf-8 -*-
# !/usr/bin/env python
from flask import Flask, render_template, request, redirect
from flask import url_for, flash, jsonify
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import SingletonThreadPool  # noqa: E402
from database_setup import Base, Restaurant, MenuItem, User  # noqa: E402
from flask import session as login_session  # noqa: E402
import random  # noqa: E402
import string  # noqa: E402
from oauth2client.client import flow_from_clientsecrets  # noqa: E402
from oauth2client.client import FlowExchangeError  # noqa: E402
import httplib2  # noqa: E402
import json  # noqa: E402
from flask import make_response  # noqa: E402
import requests  # noqa: E402
import os

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'db/restaurantmenuwithusers.db')

# Necessary for single thread pool for connection
# Creates a engine that ignore the currrent thread
# to connect within the database
engine = create_engine('sqlite:///' + DATABASE_PATH,
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

# Creates a new database session with the engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# Endpoint for a login acesss
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Endpoint just to estabilsh connection with google and webapp


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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
                                 200)
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

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;" \
                "-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User functions

# Creates a new user based on the google sign connected


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Get the information from the user
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Get the email from the user
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None

# Verify that if the user is a owner


def isUserOwner(user_id):
    user = getUserInfo(user_id)
    if user is None:
        return False
    else:
        return True


# Constant to a given unauthorized message
authorizedText = "<script>function myFunction() {alert('You are not" \
                 " authorized to this page');}</script><body onload" \
                 "='myFunction()''>"


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON endpoint for the restaurants


@app.route('/restaurants/JSON')
def getRestaurantJSON():
    restaurants = session.query(Restaurant)
    return jsonify(Restaurant=[i.serialize for i in restaurants])

# JSON endpoint for the menu items


@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def getMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    return jsonify(MenuItem=[i.serialize for i in items])

# JSON endpoint for the item


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def getMenuItemJSON(restaurant_id, menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=[item.serialize])

# Main endpoint fo te list of the restaurants
# Restricted access page for those are not owner of the restaurant


@app.route('/')
@app.route('/restaurants/')
def getRestaurants():
    restaurants = session.query(Restaurant)
    if 'username' not in login_session:
        return render_template('publicrestaurants.html',
                               restaurants=restaurants)
    else:
        return render_template('restaurants.html',
                               restaurants=restaurants)

# Endpoint to create a new restaurant


@app.route('/restaurant/new', methods=['GET', 'POST'])
def createRestaurant():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newRestaurant = Restaurant(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newRestaurant)
        session.commit()
        flash("new restaurant created!")
        return redirect(url_for('getRestaurants'))
    else:
        return render_template('newrestaurant.html')

# Endpoint to edit the selected restaurant


@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if (login_session['user_id'] is not restaurant.user_id):
        return authorizedText
    if request.method == 'POST':
        if request.form['name']:
            restaurant.name = request.form['name']
        session.add(restaurant)
        session.commit()
        flash("restaurant edited!")
        return redirect(url_for('getRestaurants'))
    else:
        return render_template('editrestaurant.html', restaurant=restaurant)

# Endpoint to delete the selected restaurant


@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if (login_session['user_id'] is not restaurant.user_id):
        return authorizedText
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash("restaurant deleted!")
        return redirect(url_for('getRestaurants'))
    else:
        return render_template('deleterestaurant.html', restaurant=restaurant)

# Endpoint to list all the menu items from a given restaurant
# Restricted access page for those are not owner of the restaurant


@app.route('/restaurant/<int:restaurant_id>/menu')
def getMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    creator = getUserInfo(restaurant.user_id)
    if 'username' not in login_session:
        return render_template('publicmenu.html',
                               restaurant=restaurant,
                               items=items,
                               creator=creator)
    return render_template(
        'menu.html', restaurant=restaurant, items=items, creator=creator)

# Endpoint to create a new menu item in the restaurant


@app.route('/restaurant/<int:restaurant_id>/menu/new', methods=['GET', 'POST'])
def createMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'],
                           description=request.form['description'],
                           price=request.form['price'],
                           course=request.form['course'],
                           restaurant_id=restaurant_id,
                           user_id=restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash("new menu item created!")
        return redirect(url_for('getMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant=restaurant)

# Endpoint to edit a menu item in the restaurant


@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit',
           methods=['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    if (login_session['user_id'] is not item.user_id):
        return authorizedText
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        session.add(item)
        session.commit()
        flash("menu item updated!")
        return redirect(url_for('getMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editmenuitem.html',
                               restaurant=restaurant, item=item)

# Endpoint to delete a menu item in the restaurant


@app.route('/restaurant/<int:restaurant_id>/'
           '<int:menu_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id=menu_id).one()
    if (login_session['user_id'] is not item.user_id):
        return authorizedText
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("menu item deleted!")
        return redirect(url_for('getMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deletemenuitem.html',
                               restaurant=restaurant,
                               item=item)


@app.errorhandler(500)
def internal_server_error(error):
    return 'Error within the request to the server', 500


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run()
