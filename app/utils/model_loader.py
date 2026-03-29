import torch

def load_convnext_checkpoint_compat(model, checkpoint_path):
    """
    Load ConvNext checkpoint with backward compatibility for key naming changes.
    
    Handles the transition from older checkpoints that use 'backbone.stages.*' keys
    to newer model architecture that uses 'backbone.model.stages.*' keys.
    
    Args:
        model: Network_ConvNext model instance
        checkpoint_path: Path to the saved checkpoint file
    """
    checkpoint = torch.load(checkpoint_path, map_location=torch.device('cpu'))
    
    # Check if we have old-style keys and remap them
    old_style_keys = [k for k in checkpoint.keys() if k.startswith('backbone.stages.')]
    
    if old_style_keys:
        # Remap old keys to new format
        new_checkpoint = {}
        for key, value in checkpoint.items():
            if key.startswith('backbone.stages.'):
                # Convert 'backbone.stages.*' to 'backbone.model.stages.*'
                new_key = key.replace('backbone.stages.', 'backbone.model.stages.')
                new_checkpoint[new_key] = value
            else:
                new_checkpoint[key] = value
        checkpoint = new_checkpoint
    
    # Load with strict=False to tolerate minor architecture differences
    model.load_state_dict(checkpoint)
