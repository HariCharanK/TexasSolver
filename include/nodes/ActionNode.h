//
// Created by Xuefeng Huang on 2020/1/30.
//

#ifndef TEXASSOLVER_ACTIONNODE_H
#define TEXASSOLVER_ACTIONNODE_H


#include <include/trainable/Trainable.h>
#include <thread>
#include <mutex>
#include <include/ranges/PrivateCards.h>
#include "include/nodes/GameTreeNode.h"
#include "include/nodes/GameActions.h"

class ActionNode :public GameTreeNode {
public:
    ActionNode(vector<GameActions> actions, vector<shared_ptr<GameTreeNode>> childrens, int player, GameRound round,double pot,shared_ptr<GameTreeNode> parent);
    ~ActionNode();
    vector<GameActions>& getActions();
    vector<shared_ptr<GameTreeNode>>& getChildrens();
    int getPlayer();
    shared_ptr<Trainable> getTrainable(int i,bool create_on_site=true,int use_halffloats=0);
    void setTrainable(vector<shared_ptr<Trainable>> trainable,vector<PrivateCards>* player_privates);
    vector<PrivateCards>* player_privates;

    // Node locking: freeze this node's strategy so CFR treats it as a fixed opponent model.
    // freqs maps action names ("fold","call","raise","check","bet") to probabilities.
    // Probabilities are normalised automatically; unspecified actions get 0.
    void lockNode(const map<string,float>& freqs);
    bool isLocked() const;
    vector<float> getLockedStrategy(int n_hands) const;
    const vector<float>& getLockedProbs() const;

private:
    GameTreeNodeType getType() override;
private:
    vector<GameActions> actions;
public:
    void setActions(const vector<GameActions> &actions);
    void setChildrens(const vector<shared_ptr<GameTreeNode>> &childrens);

private:
    vector<shared_ptr<GameTreeNode>> childrens;
    vector<shared_ptr<Trainable>> trainables;
    int player;

    bool is_locked = false;
    vector<float> locked_probs; // one probability per action, uniform across all hands
};


#endif //TEXASSOLVER_ACTIONNODE_H
