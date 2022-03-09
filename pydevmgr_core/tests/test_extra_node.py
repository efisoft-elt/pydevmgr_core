from pydevmgr_core import *

if False:
    from matplotlib.pylab import plt
    use_plot = True
else:
    use_plot = False

def test_main():
    
    try:
        import numpy
    except ModuleNotFoundError:
        print( "Warning numpy related node cannot be tested : numpy not installed" )
        return 
    
    s = StaticNode(value=16)
    v = NoiseAdderNode(node=s, scale=4)

    st = StatisticNode(node=v, mean=16)

    h = HistogramNode(node=v, bins=(0,32,33))
    for i in range(10000):
        _st, _h = download( [st, h] )
        
    print(_st)
    if use_plot:
        plt.bar( (h._bins[:-1]+h._bins[1:])/2,_h)
        plt.axvline(_st.mean, color="red")
        plt.show()

if __name__ == "__main__":
    test_main()
