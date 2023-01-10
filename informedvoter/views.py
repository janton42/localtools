from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# from .forms import

# Import any models needed for views. Note: all views accessing db should require login
# from .models import

# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName

# These pages are accessible without a login.

def index(request):
    return render(request, 'index.html')
