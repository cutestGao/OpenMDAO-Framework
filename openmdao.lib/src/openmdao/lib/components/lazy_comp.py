from openmdao.main.api import Component


class LazyComponent(Component): 
    """
    Base Component Class for situations where you want your component to calculate 
    only the output values that are connected to something else in the model. This 
    behavior makes the component "lazy" since some of its outputs won't be valid 
    even though it has executed. 

    The component provides an attribute which can be used in the 'execute' method
    called '_connected_outputs' which lists all the outputs that are connected to something
    in your model. You need not calculate any outputs that are not in that list, but 
    note that the list is not static and could change from run to run. So 
    you do need to make sure that you could potentially calculate all 
    your outputs if requested. 

    Note that there is some extra framework overhead associated with this base class. So you 
    should only use it in the case where you have outputs that are computationally expensive 
    and you wish to only calculate them when they are relevant to the current simulation. 
    """
    def _pre_execute(self, force=False): 
        super(LazyComponent, self)._pre_execute()
        if self.parent:
            self._connected_outputs = self.parent._depgraph.list_outputs(self.name, 
                                                                       connected=True)
        else:
            self._connected_outputs = []

    def _outputs_to_validate(self):
        return self._connected_outputs
