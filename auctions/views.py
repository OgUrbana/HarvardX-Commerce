from locale import currency
from pydoc import describe
from turtle import isdown
from unicodedata import category
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid


def index(request):
    activeListings = Listing.objects.filter(isActive=True)
    categories = Category.objects.all()

    return render(request, "auctions/index.html", {
        "Listings": activeListings,
        "categories": categories
    })

def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    checkWatchlist = request.user in listingData.watchlist.all()
    getComments = Comment.objects.filter(listing=listingData)

    checkOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "checkWatchlist": checkWatchlist,
        "allComments": getComments,
        "checkOwner": checkOwner
    })

def endAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    checkOwner = request.user.username == listingData.owner.username
    checkWatchlist = request.user in listingData.watchlist.all()
    getComments = Comment.objects.filter(listing=listingData)

    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "checkWatchlist": checkWatchlist,
        "allComments": getComments,
        "checkOwner": checkOwner,
        "update": True,
        "message": "You have ended the auction!"
    })

def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currUser = request.user
    listingData.watchlist.remove(currUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currUser = request.user
    listingData.watchlist.add(currUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def watchlist(request):
    currUser = request.user
    listings = currUser.listingWatchlist.all()

    return render(request, "auctions/watchlist.html",{
        "Listings": listings
    })

def addComment(request, id):
    currUser = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST['getComment']

    newComment = Comment(
        author=currUser,
        listing=listingData,
        message=message
    )

    newComment.save()
    
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def displayCategory(request):
    if request.method == "POST":
        categoryPicked = request.POST['category']
        category = Category.objects.get(categoryName=categoryPicked)
        activeListings = Listing.objects.filter(isActive=True, category=category)
        categories = Category.objects.all()

        return render(request, "auctions/index.html", {
            "Listings": activeListings,
            "categories": categories
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def addBid(request, id):
    newBid = request.POST['getBid']
    listingData = Listing.objects.get(pk=id)
    checkWatchlist = request.user in listingData.watchlist.all()
    getComments = Comment.objects.filter(listing=listingData)

    if int(newBid) > listingData.price.bid:
        updateBid = Bid(user=request.user, bid=int(newBid))
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Successfully bid!",
            "update": True,
            "checkWatchlist": checkWatchlist,
            "allComments": getComments
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Failed to bid!",
            "update": False,
            "checkWatchlist": checkWatchlist,
            "allComments": getComments
        })

def create(request):
        
    if request.method == 'GET':
        categories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": categories
        })

    elif request.method == 'POST':
        title = request.POST["title"]
        price = request.POST["bid"]
        image = request.POST["image"]
        description = request.POST["desc"]
        category = request.POST["category"]

        activeUser = request.user

        categoryData = Category.objects.get(categoryName=category)
        
        bid = Bid(bid=int(price), user=activeUser)
        bid.save()
        newListing = Listing(
            title=title,
            description=description,
            imageUrl=image,
            price=bid,
            category=categoryData ,
            owner=activeUser
        )

        newListing.save()
        return HttpResponseRedirect(reverse(index))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
