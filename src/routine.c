/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   routine.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: asaadane <asaadane@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/02 23:04:03 by asaadane          #+#    #+#             */
/*   Updated: 2026/11/18 19:43:00 by asaadane         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "philo.h"

// Announce actions of philosophers with mutex synchronization
void	manage_philos(t_info *philo, t_moves action)
{
	if (action == DIE)
		printf(DEATH, ft_time() - philo->start, philo->id);
	else
	{
		pthread_mutex_lock(philo->sync);
		if (action == FORK_TAKEN)
			printf(TAKING_FORKS, ft_time() - philo->start, philo->id);
		else if (action == EAT)
		{
			printf(EATING, ft_time() - philo->start, philo->id);
			philo->last_meal = ft_time();
		}
		else if (action == SLEEP)
			printf(SLEEPING, ft_time() - philo->start, philo->id);
		else if (action == THINK)
			printf(THINKING, ft_time() - philo->start, philo->id);
		pthread_mutex_unlock(philo->sync);
	}
}

// Pick up forks with resource ordering hierarchy to prevent deadlocks
static void	pick_fork(t_info *philo)
{
	pthread_mutex_t	*first;
	pthread_mutex_t	*second;

	if (philo->left_fork < philo->right_fork)
	{
		first = philo->left_fork;
		second = philo->right_fork;
	}
	else
	{
		first = philo->right_fork;
		second = philo->left_fork;
	}
	pthread_mutex_lock(first);
	manage_philos(philo, FORK_TAKEN);
	pthread_mutex_lock(second);
	manage_philos(philo, FORK_TAKEN);
}

// Philosopher eat routine
void	eat(t_info *philo)
{
	pick_fork(philo);
	manage_philos(philo, EAT);
	ft_usleep(philo->t_eat);
	pthread_mutex_lock(philo->sync);
	philo->eating_time++;
	pthread_mutex_unlock(philo->sync);
	pthread_mutex_unlock(philo->left_fork);
	pthread_mutex_unlock(philo->right_fork);
}

// Philosopher sleep routine
void	philo_sleep(t_info *philo)
{
	manage_philos(philo, SLEEP);
	ft_usleep(philo->t_sleep);
}

// Philosopher think routine
void	philo_think(t_info *philo)
{
	manage_philos(philo, THINK);
}
