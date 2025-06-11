import logging

from django.utils import timezone
from django.utils.timezone import localtime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Booking, FitnessClass
from .serializers import BookingSerializer, FitnessClassSerializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_classes(request):
    try:
        classes = FitnessClass.objects.filter(datetime__gte=timezone.now()).order_by('datetime')
        serializer = FitnessClassSerializer(classes, many=True)
        logger.info(f"{len(classes)} upcoming classes fetched")
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error fetching classes: {str(e)}")
        return Response({'error': 'Failed to fetch classes'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def book_class(request):
    data = request.data
    logger.debug(f"Request data: {data}")

    required_fields = ['fitness_class', 'client_name', 'client_email']
    for field in required_fields:
        if field not in data:
            logger.warning(f"Missing required field: {field}")
            return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fitness_class = FitnessClass.objects.get(id=data['fitness_class'])
        logger.debug(f"Fitness class found: {fitness_class.name}")
    except FitnessClass.DoesNotExist:
        logger.warning(f"Fitness class ID {data['fitness_class']} does not exist")
        return Response({'error': 'Fitness class does not exist'}, status=status.HTTP_404_NOT_FOUND)

    if fitness_class.datetime < timezone.now():
        logger.warning("Attempt to book a past class")
        return Response({'error': 'Cannot book past classes'}, status=status.HTTP_400_BAD_REQUEST)

    if fitness_class.available_slots <= 0:
        logger.warning("Attempt to book a full class")
        return Response({'error': 'No available slots'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = BookingSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        fitness_class.available_slots -= 1
        fitness_class.save()
        logger.info(f"Booking created: {data['client_name']} for {fitness_class.name}")
        return Response({'message': 'Booking successful'}, status=status.HTTP_201_CREATED)
    else:
        logger.warning(f"Invalid booking attempt: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_bookings_by_email(request):
    email = request.GET.get('email')
    if not email:
        logger.warning("Email parameter missing in request")
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    bookings = Booking.objects.filter(client_email=email)
    logger.info(f"{bookings.count()} bookings found for email: {email}")

    data = [{
        'class_name': b.fitness_class.name,
        'datetime': localtime(b.fitness_class.datetime).strftime('%Y-%m-%d %H:%M:%S'),
        'instructor': b.fitness_class.instructor
    } for b in bookings]
    return Response(data)
