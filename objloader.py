import pygame
from OpenGL.GL import *

def MTL(dir, filename): 
    """[summary] Load the material file  

    Arguments:
        dir {[type]} -- [description]
        filename {[type]} -- [description]

    Returns:
        [type] -- [description]
    """

    contents = {} # Store the contents of the mtl file  
    mtl = None # The current material  
    for line in open(dir + filename, "r"): # Go through each line in the file  
        if line.startswith('#'): continue # If the first character is a #, it is a comment, so ignore it  
        values = line.split() # Split the line using spaces  
        if not values: continue # If there is nothing in the line, ignore it  
        if values[0] == 'newmtl': # If the line starts with newmtl, create a new material  
            mtl = contents[values[1]] = {} # Add a new dictionary entry to contents  
        elif mtl is None: # If there is no material, throw an error     
            raise (ValueError, "mtl file doesn't start with newmtl stmt") # Store the values under their appropriate keys 
        elif values[0] == 'map_Kd': # If the line starts with map_Kd, load the texture referred to by the line 
            # load the texture referred to by this declaration
            mtl[values[0]] = dir + values[1] 
            surf = pygame.image.load(mtl['map_Kd']) # Load the texture file 
            image = pygame.image.tostring(surf, 'RGBA', 1) # Convert the image to RGBA format 
            ix, iy = surf.get_rect().size # Store the original width and height of the image 
            texid = mtl['texture_Kd'] = glGenTextures(1) # Generate a texture ID 
            # print('texid', texid)  
            # texid = 10  
            glBindTexture(GL_TEXTURE_2D, texid) # Bind the texture  
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,  # Set the texture minification and magnification filters
                GL_LINEAR) # to GL_LINEAR (this is important. Note that OpenGL  # is dumb and you need to specify GL_LINEAR twice) 
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, # Set the texture minification and magnification filters   
                GL_LINEAR) # to GL_LINEAR  (this is important. Note that OpenGL  # is dumb and you need to specify GL_LINEAR twice)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, ix, iy, 0, GL_RGBA, # Set the texture data for OpenGL   
                GL_UNSIGNED_BYTE, image) # to use the image we loaded   
        else:  # Otherwise, store the values in their appropriate place
            mtl[values[0]] = list(map(float, values[1:])) # Store the values in the dictionary
    return contents # Return the contents of the mtl file 

# TODO load more format models
class OBJ:
    def __init__(self, filename, swapyz=False): # Load the model from a file. 
        
        self.dir = filename[: filename.rfind('/') + 1] # Get the directory the file is in         
        
        """Loads a Wavefront OBJ file. """ 
        self.vertices = [] # List of vertices 
        self.normals = [] # List of normals
        self.texcoords = [] # List of texture coordinates
        self.faces = [] # List of faces 

        material = None # The current material being used
        for line in open(filename, "r"): # Go through each line in the file
            if line.startswith('#'): continue # If the first character is a #, it is a comment, so ignore it
            values = line.split() # Split the line using spaces 
            if not values: continue # If there is nothing in the line, ignore it 
            
            if values[0] == 'v': # If the line starts with v, it is a vertex, so add it to the list of vertices
                v = list(map(float, values[1:4])) # Convert the vertex coordinates to floats 
                if swapyz: # If the swapyz flag is set, swap the y and z coordinates
                    v = v[0], v[2], v[1] # Swap the y and z coordinates 
                self.vertices.append(v) # Add the vertex to the list of vertices 
            elif values[0] == 'vn': # If the line starts with vn, it is a normal, so add it to the list of normals
                v = list(map(float, values[1:4])) # Convert the normal coordinates to floats 
                if swapyz: # If the swapyz flag is set, swap the y and z coordinates
                    v = v[0], v[2], v[1] # Swap the y and z coordinates
                self.normals.append(v) # Add the normal to the list of normals
            elif values[0] == 'vt': # If the line starts with vt, it is a texture coordinate, so add it to the list of texture coordinates 
                self.texcoords.append(list(map(float, values[1:3]))) # Convert the texture coordinates to floats  
            elif values[0] in ('usemtl', 'usemat'): # If the line starts with usemtl or usemat, it is a material declaration, so get the material name 
                material = values[1] # Get the material name 
                # print('debug values', values[1]) 
            elif values[0] == 'mtllib': # If the line starts with mtllib, it is a material library, so load it 
                self.mtl = MTL(self.dir, values[1]) # Load the material library 
            elif values[0] == 'f': # If the line starts with f, it is a face, so add it to the list of faces 
                face = [] # Create a list for the face 
                texcoords = [] # Create a list for the texture coordinates  
                norms = [] # Create a list for the normals   
                for v in values[1:]: # Go through each vertex in the face   
                    w = v.split('/') # Split the vertex into its constituent parts   
                    face.append(int(w[0])) # Add the vertex index to the face list  
                    if len(w) >= 2 and len(w[1]) > 0:  # If there is a texture coordinate, add it to the texture coordinate list   
                        texcoords.append(int(w[1])) # Add the texture coordinate index to the texture coordinate list  
                    else: # Otherwise, add 0 to the texture coordinate list  
                        texcoords.append(0) # Add 0 to the texture coordinate list 
                    if len(w) >= 3 and len(w[2]) > 0: # If there is a normal, add it to the normal list 
                        norms.append(int(w[2])) # Add the normal index to the normal list 
                    else: # Otherwise, add 0 to the normal list 
                        norms.append(0) # Add 0 to the normal list 
                self.faces.append((face, norms, texcoords, material)) # Add the face to the list of faces 
            elif values[0] == 'o':
                self.name = values[1]

        self.gl_list = glGenLists(1) # Generate a display list 
        glNewList(self.gl_list, GL_COMPILE) # Compile the display list 
        glFrontFace(GL_CCW)  # Front faces are counter-clockwise
        for face in self.faces: # Go through each face in the faces list
            vertices, normals, texture_coords, material = face # Get the vertices, normals, texture coordinates and material for the face 
            mtl = self.mtl[material] # Get the material from the material list
            if 'texture_Kd' in mtl: # If there is a diffuse texture, bind it to GL_TEXTURE_2D 
                # use diffuse texmap 
                glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd']) # Bind the texture  
            else: # Otherwise, use the diffuse colour 
                # just use diffuse colour
                glColor3f(*mtl['Kd']) # Set the diffuse colour 
            glBegin(GL_POLYGON)             # Begin drawing the face
            for i in range(len(vertices)): # Go through each vertex in the face 
                if normals[i] > 0: # If there is a normal index, use it 
                    glNormal3fv(self.normals[normals[i] - 1]) # Set the normal 
                if texture_coords[i] > 0 and 'texture_Kd' in mtl: # If there is a texture coordinate index and a diffuse texture, use it 
                    glTexCoord2fv(self.texcoords[texture_coords[i] - 1]) # Set the texture coordinate 
                glVertex3fv(self.vertices[vertices[i] - 1]) # Set the vertex 
            glEnd()
        glColor3f(1.0,1.0,1.0) # Clear the painting color.
        glEndList()