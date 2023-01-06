from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

from .forms import UserRegistrationForm

# Import any models needed for views. Note: all views accessing db should require login
# from .models import ModelName, OtherModel, AnotherOne

# Import other python packages, includes ones you wrote. "script_name" is the name of the .py file
# containing ClassName, which is the desired import

# from .top_level.package_directory.script_name import ClassName 

# These pages are accessible without a login.

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method =='POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, 'Your account has been created.\n\
            You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    context = {'form': form}
    return render(request, 'register.html', context)



# All views below require login

#@login_required
#def page_with_content_from_db(request):
#    db_objects_to_display = TableName.objects.all()\
#    .filter(user=request.user)\
#    .values()
#    context = {
#        'db_objects_to_display': db_objects_to_display
#    }
#    return render(request,'page_template.html', context)
