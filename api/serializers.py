from rest_framework import serializers

class CustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    email = serializers.EmailField(max_length=255)

class CustomerUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, required=False)
    email = serializers.EmailField(max_length=255, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "At least one field must be provided."
            )
        
        return attrs