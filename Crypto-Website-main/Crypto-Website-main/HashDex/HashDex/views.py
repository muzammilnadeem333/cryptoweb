from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse





@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def index_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard/')  # Replace 'dashboard' with your URL name
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})




@login_required
def run_account_checks(request):
    if request.method =='POST':
        pass

    else:
        return render(request , 'error404.html')