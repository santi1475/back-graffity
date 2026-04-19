import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

from django.contrib.auth import get_user_model
from pos.models import Product, Brand, Category

User = get_user_model()

class ProductScannerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='testpassword')
        self.client.force_authenticate(user=self.user)
        
        self.brand = Brand.objects.create(name="Brand 1", is_active=True)
        self.category = Category.objects.create(title="Category 1", is_active=True)
        
        self.product = Product.objects.create(
            title="Test Product Scanner",
            sku="SCN-123",
            price_general=10.00,
            brand=self.brand,
            category=self.category,
            state=1
        )
        self.channel_uuid = str(uuid.uuid4())
        self.scan_url = reverse('product-scan')  # Asegúrate de que el name en urls.py sea 'product-scan'
        
    def test_scan_missing_params(self):
        """Si falta barcode o channel_uuid debe retornar 400."""
        response = self.client.post(self.scan_url, {'barcode': '123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.post(self.scan_url, {'channel_uuid': self.channel_uuid})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('pos.services.get_channel_layer')
    def test_scan_valid_product(self, mock_get_channel_layer):
        """Simula enviar un escaneo y verifica que intente enviarlo por websockets."""
        mock_channel_layer = mock_get_channel_layer.return_value
        
        # Enviamos codigo
        data = {
            'barcode': 'SCN-123',
            'channel_uuid': self.channel_uuid
        }
        response = self.client.post(self.scan_url, data, format='json')
        
        # Validar la respuesta HTTP
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['product_found'])
        self.assertEqual(response.data['product_name'], self.product.title)
        
        # Verificar que Django Channels fue llamado
        if mock_channel_layer:
            mock_channel_layer.group_send.assert_called_once()
            args, kwargs = mock_channel_layer.group_send.call_args
            
            # args[0] es el channel name (scan_{uuid})
            self.assertEqual(args[0], f"scan_{self.channel_uuid}")
            # args[1] es el mensaje
            self.assertEqual(args[1]['type'], "product.scanned")
            self.assertEqual(args[1]['barcode'], 'SCN-123')
            self.assertIsNotNone(args[1]['productData'])
            self.assertEqual(args[1]['productData']['sku'], 'SCN-123')

    @patch('pos.services.get_channel_layer')
    def test_scan_invalid_product(self, mock_get_channel_layer):
        """Simula escanear un producto inexistente."""
        mock_channel_layer = mock_get_channel_layer.return_value
        
        data = {
            'barcode': 'NOEXISTE-999',
            'channel_uuid': self.channel_uuid
        }
        response = self.client.post(self.scan_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['product_found'])
        self.assertIsNone(response.data['product_name'])
        
        # Verifica que igual dispara el evento de websocket, útil para avisar al admin 
        # que leyó un scanner que no corresponde a ningún producto en la bd
        if mock_channel_layer:
            mock_channel_layer.group_send.assert_called_once()
            args, kwargs = mock_channel_layer.group_send.call_args
            self.assertEqual(args[1]['type'], "product.scanned")
            self.assertEqual(args[1]['barcode'], 'NOEXISTE-999')
            self.assertIsNone(args[1]['productData'])
