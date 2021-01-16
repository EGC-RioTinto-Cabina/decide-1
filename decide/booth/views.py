import json
import datetime

from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404

from base import mods
from voting.models import Voting
from census.models import Census
from store.models import Vote
from django.shortcuts import render, redirect 
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.http import HttpResponseForbidden
from .forms import CrearUsuario
from .forms import PeticionForm
from .models import PeticionCenso

# Create your views here.


# TODO: check permissions and census
class BoothView(TemplateView):
    template_name = 'booth/booth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vid = kwargs.get('voting_id', 0)

        try:
            r = mods.get('voting', params={'id': vid})

            # Casting numbers to string to manage in javascript with BigInt
            # and avoid problems with js and big number conversion
            for k, v in r[0]['pub_key'].items():
                r[0]['pub_key'][k] = str(v)

            context['voting'] = json.dumps(r[0])
        except:
            raise Http404

        context['KEYBITS'] = settings.KEYBITS

        return context
    
    def get_format_date(self, fecha):
        result = None

        if fecha != None:
            fecha = fecha.replace("T", " ").replace("Z", "")
            date_time = datetime.datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S.%f')
            result = date_time.strftime('%d/%m/%Y a las %H:%M:%S')

        return result 

    
def prueba(request):
    return render(request, "booth/booth.html")


def loginPage(request):
	    if request.user.is_authenticated:
		    return redirect('welcome')
	    else:
		    if request.method == 'POST':
			    username = request.POST.get('username')
			    password = request.POST.get('password')

			    user = authenticate(request, username=username, password=password)

			    if user is not None:
				    login(request, user)
				    return redirect('welcome')
			    else:
				    messages.info(request, 'Usuario o contraseña incorrectos')

		    context = {}
		    return render(request, 'booth/login.html', context)

def welcome(request):
	context={}
	listaUltimasVotaciones=[]
	listaUltimasVotaciones=ultimasVotaciones()
	listaCensada=listaCensadaIds(request.user.id)
	votacionesUsuarioCensado=votacionesPorUsuario(listaCensada, request.user.id)
	context = {'allVotaciones':listaUltimasVotaciones, 'votacionesCensado':votacionesUsuarioCensado, 'listaVacia':False}
	if len(votacionesUsuarioCensado)==0:
		context['listaVacia']=True
	return render(request, "booth/welcome.html", context)


@login_required(login_url='login')
def peticionCensoAdmin(request):
	context={}
	if not request.user.is_superuser:
		return HttpResponseForbidden()
	else:
		listaUltimasPeticiones=[]
		listaUltimasPeticiones=ultimasPeticiones()
		context = {'allPeticiones':listaUltimasPeticiones, 'listaVacia':False}
		if len(listaUltimasPeticiones)==0:
			context['listaVacia']=True
		return render(request, "booth/peticionCensoAdmin.html", context)

@login_required(login_url='login')
def peticionCensoUsuario(request):
	form = PeticionForm()
	if request.method == 'POST':
		form = PeticionForm(request.POST)
		if form.is_valid():
			obj = form.save(commit=False)
			obj.user_id = request.user.id
			obj.save()

			return redirect('welcome')
			

	context = {'form':form}
	return render(request, 'booth/peticionCensoUsuario.html', context)


def logoutUser(request):
	logout(request)
	return redirect('welcome')


def registerPage(request):
	if request.user.is_authenticated:
		return redirect('welcome')
	else:
		form = CrearUsuario()
		if request.method == 'POST':
			form = CrearUsuario(request.POST)
			if form.is_valid():
				form.save()
				user = form.cleaned_data.get('username')

				return redirect('login')
			

		context = {'form':form}
		return render(request, 'booth/register.html', context)


def votacionesPorUsuario(votacionesId, user_id):
	listaVotaciones=[]
	totalVotaciones = Voting.objects.all().filter(id__in=votacionesId, end_date__isnull=True)
	for v in totalVotaciones:
		votos = Vote.objects.filter(voting_id=v.id, voter_id=user_id)
		if votos.count()==0:
			listaVotaciones.append(v)
	
	return listaVotaciones

def ultimasVotaciones():
	listaVotaciones=[]
	totalVotaciones = Voting.objects.all().filter(end_date__isnull=True).order_by('-start_date')
	for v in totalVotaciones:
		listaVotaciones.append(v)
	return listaVotaciones

def listaCensadaIds(user_id):
	listaCensadaIds = []
	totalListaCensada = Census.objects.all().filter(voter_id=user_id)
	if totalListaCensada.count() != 0:
		for c in totalListaCensada:
			listaCensadaIds.append(c.voting_id)

	return listaCensadaIds

def ultimasPeticiones():
	listaPeticiones=[]
	totalPeticiones = PeticionCenso.objects.all()
	for t in totalPeticiones:
		listaPeticiones.append(t)
	return listaPeticiones